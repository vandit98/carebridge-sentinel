from __future__ import annotations

import json
import os
import asyncio
import ipaddress
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import jwt
from mcp.server.fastmcp import Context

from carebridge_sentinel.constants import (
    FHIR_ACCESS_TOKEN_HEADER,
    FHIR_SERVER_URL_HEADER,
    PATIENT_ID_HEADER,
)
from carebridge_sentinel.privacy import redact


@dataclass(frozen=True)
class FhirContext:
    base_url: str | None
    token: str | None
    patient_id: str | None
    synthetic: bool = False


class FhirClient:
    """Small async FHIR R4 client scoped to read/search operations."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        validate_fhir_base_url(base_url)
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any] | None:
        headers = {"Accept": "application/fhir+json, application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(self._build_url(path), headers=headers, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def read(self, path: str) -> dict[str, Any] | None:
        return await self._get(path)

    async def search(
        self,
        resource_type: str,
        search_parameters: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        return await self._get(resource_type, params=search_parameters)


class SyntheticFhirClient:
    """Read-only fixture-backed FHIR client for local demos and tests."""

    def __init__(self, fixture_path: Path | None = None) -> None:
        fixture = fixture_path or Path(__file__).resolve().parent.parent / "examples" / "synthetic_patient_bundle.json"
        self.bundle = json.loads(fixture.read_text())
        self.resources = [entry["resource"] for entry in self.bundle.get("entry", []) if entry.get("resource")]

    async def read(self, path: str) -> dict[str, Any] | None:
        resource_type, _, resource_id = path.partition("/")
        for resource in self.resources:
            if resource.get("resourceType") == resource_type and resource.get("id") == resource_id:
                return resource
        return None

    def patient_ids(self) -> list[str]:
        return [
            str(resource["id"])
            for resource in self.resources
            if resource.get("resourceType") == "Patient" and resource.get("id")
        ]

    async def search(
        self,
        resource_type: str,
        search_parameters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        params = search_parameters or {}
        patient_id = params.get("patient")
        matches: list[dict[str, Any]] = []

        for resource in self.resources:
            if resource.get("resourceType") != resource_type:
                continue
            if patient_id and not _resource_mentions_patient(resource, patient_id):
                continue
            matches.append({"resource": resource})

        return {"resourceType": "Bundle", "type": "searchset", "entry": matches}


def synthetic_mode_enabled() -> bool:
    return os.getenv("CAREBRIDGE_SYNTHETIC_FHIR", "").lower() in {"1", "true", "yes", "on"}


def get_fhir_context(ctx: Context | None) -> FhirContext:
    if ctx is None:
        return FhirContext(base_url=None, token=None, patient_id=None, synthetic=synthetic_mode_enabled())

    request = ctx.request_context.request
    base_url = request.headers.get(FHIR_SERVER_URL_HEADER)
    token = request.headers.get(FHIR_ACCESS_TOKEN_HEADER)
    patient_id = request.headers.get(PATIENT_ID_HEADER)

    if not patient_id and token:
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
            patient = claims.get("patient")
            if patient:
                patient_id = str(patient)
        except jwt.PyJWTError:
            pass

    return FhirContext(
        base_url=base_url,
        token=token,
        patient_id=patient_id,
        synthetic=synthetic_mode_enabled() and not base_url,
    )


def get_client(context: FhirContext) -> FhirClient | SyntheticFhirClient:
    if context.synthetic:
        return SyntheticFhirClient()
    if not context.base_url:
        raise ValueError(
            "FHIR context is missing. In Prompt Opinion, enable the FHIR context extension. "
            "For local demo mode, set CAREBRIDGE_SYNTHETIC_FHIR=true."
        )
    return FhirClient(context.base_url, context.token)


def validate_fhir_base_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("FHIR server URL must be an absolute http(s) URL.")

    if parsed.scheme != "https" and not _truthy_env("CAREBRIDGE_ALLOW_INSECURE_FHIR"):
        raise ValueError("FHIR server URL must use HTTPS unless CAREBRIDGE_ALLOW_INSECURE_FHIR=true.")

    host = parsed.hostname or ""
    allowed_hosts = _csv_env("CAREBRIDGE_ALLOWED_FHIR_HOSTS")
    if allowed_hosts and host not in allowed_hosts:
        raise ValueError("FHIR server host is not in CAREBRIDGE_ALLOWED_FHIR_HOSTS.")

    if not allowed_hosts and _is_blocked_host(host):
        raise ValueError("FHIR server URL points to a local/private host. Set CAREBRIDGE_ALLOWED_FHIR_HOSTS to allow it.")


def resolve_patient_id(explicit_patient_id: str | None, context: FhirContext) -> str:
    patient_id = explicit_patient_id or context.patient_id
    if patient_id:
        return patient_id
    if context.synthetic:
        return "synthetic-patient-001"
    raise ValueError("No patient ID was supplied and no patient context was available.")


async def safe_search(
    client: FhirClient | SyntheticFhirClient,
    resource_type: str,
    params: dict[str, str],
) -> tuple[list[dict[str, Any]], str | None]:
    try:
        bundle = await client.search(resource_type, params)
        entries = bundle.get("entry", []) if bundle else []
        return [entry["resource"] for entry in entries if entry.get("resource")], None
    except Exception as exc:
        return [], f"{resource_type}: {exc}"


async def fetch_patient_record(
    client: FhirClient | SyntheticFhirClient,
    patient_id: str,
    lookback_days: int,
) -> dict[str, Any]:
    patient = await client.read(f"Patient/{patient_id}")
    if not patient:
        raise ValueError(f"Patient/{patient_id} could not be found.")

    searches = {
        "Encounter": {"patient": patient_id, "_count": "50", "_sort": "-date"},
        "Condition": {"patient": patient_id, "_count": "100"},
        "Observation": {"patient": patient_id, "_count": "200", "_sort": "-date"},
        "MedicationRequest": {"patient": patient_id, "_count": "100"},
        "MedicationStatement": {"patient": patient_id, "_count": "100"},
        "AllergyIntolerance": {"patient": patient_id, "_count": "50"},
        "Appointment": {"patient": patient_id, "_count": "50", "_sort": "date"},
        "CarePlan": {"patient": patient_id, "_count": "50"},
        "ServiceRequest": {"patient": patient_id, "_count": "50"},
        "Procedure": {"patient": patient_id, "_count": "100", "_sort": "-date"},
        "Immunization": {"patient": patient_id, "_count": "100", "_sort": "-date"},
        "DocumentReference": {"patient": patient_id, "_count": "50", "_sort": "-date"},
    }

    results = await asyncio.gather(
        *(safe_search(client, resource_type, params) for resource_type, params in searches.items())
    )

    record: dict[str, Any] = {"Patient": [patient], "_errors": [], "_lookbackDays": lookback_days}
    for resource_type, (resources, error) in zip(searches.keys(), results, strict=True):
        record[resource_type] = resources
        if error:
            record["_errors"].append(redact(error))

    return record


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str) -> set[str]:
    return {item.strip() for item in os.getenv(name, "").split(",") if item.strip()}


def _is_blocked_host(host: str) -> bool:
    if host in {"localhost", "metadata.google.internal"}:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved


def _resource_mentions_patient(resource: dict[str, Any], patient_id: str) -> bool:
    expected = f"Patient/{patient_id}"
    candidates = [
        resource.get("patient", {}).get("reference"),
        resource.get("subject", {}).get("reference"),
        resource.get("beneficiary", {}).get("reference"),
    ]
    for participant in resource.get("participant") or []:
        actor = participant.get("actor") or {}
        candidates.append(actor.get("reference"))
    return expected in candidates
