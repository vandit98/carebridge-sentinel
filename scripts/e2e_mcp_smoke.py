from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

import httpx


BASE_URL = os.getenv("CAREBRIDGE_E2E_BASE_URL", "http://127.0.0.1:8765")
MCP_URL = f"{BASE_URL}/mcp"
TOOLS = {
    "GenerateTransitionOfCareBrief": {"lookbackDays": 45},
    "FindLongitudinalCareGaps": {"lookbackDays": 365},
    "BuildMedicationSafetyBrief": {"lookbackDays": 365},
    "DraftPatientOutreach": {"channel": "phone", "lookbackDays": 45},
    "CreatePostDischargeRescuePlan": {"lookbackDays": 45},
    "GenerateTransitionTaskBundle": {"lookbackDays": 45},
    "PrioritizeTransitionPanel": {"lookbackDays": 45, "maxPatients": 10},
}


def main() -> None:
    process = None
    if "CAREBRIDGE_E2E_BASE_URL" not in os.environ:
        env = os.environ.copy()
        env["CAREBRIDGE_SYNTHETIC_FHIR"] = "true"
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "carebridge_sentinel.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_health()

    try:
        initialized = rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "carebridge-e2e-smoke", "version": "0.1.0"},
        })
        extensions = initialized["result"]["capabilities"].get("extensions", {})
        assert "ai.promptopinion/fhir-context" in extensions, "FHIR context extension missing"

        listed = rpc("tools/list", {})
        names = {tool["name"] for tool in listed["result"]["tools"]}
        missing = TOOLS.keys() - names
        assert not missing, f"Missing tools: {sorted(missing)}"

        for name, arguments in TOOLS.items():
            result = rpc("tools/call", {"name": name, "arguments": arguments})
            text = result["result"]["content"][0]["text"]
            assert "Safety note:" in text, f"{name} did not include a safety note"
            assert "synthetic-patient-001" in text, f"{name} did not use synthetic patient context"

        print("E2E MCP smoke test passed:")
        print(f"- initialize advertises FHIR context scopes")
        print(f"- tools/list includes {len(TOOLS)} CareBridge tools")
        print(f"- all tool calls returned cited synthetic clinical output")
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def wait_for_health() -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            response = httpx.get(f"{BASE_URL}/healthz", timeout=1)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.2)
    raise RuntimeError("Server did not become healthy.")


def rpc(method: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": method, "method": method, "params": params}
    response = httpx.post(
        MCP_URL,
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return parse_sse_json(response.text)


def parse_sse_json(text: str) -> dict[str, Any]:
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line.removeprefix("data: "))
    raise ValueError(f"No JSON-RPC data event found: {text[:200]}")


if __name__ == "__main__":
    main()
