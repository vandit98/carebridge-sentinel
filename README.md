# CareBridge Sentinel MCP

CareBridge Sentinel is a Prompt Opinion-compatible healthcare MCP server for transitions of care, medication safety, and longitudinal care-gap review.

It is built for the **Agents Assemble - The Healthcare AI Endgame** hackathon path:

- **Path A: MCP Server** that exposes specialized healthcare tools.
- **SHARP/FHIR context support** through `ai.promptopinion/fhir-context`.
- **Synthetic/de-identified local demo mode** for development and video prep.
- **No PHI storage**. FHIR credentials are read from request headers at tool-call time.

## Why This Can Win

Judges score equally on:

- **AI Factor**: the tools produce structured, cited FHIR evidence that a generative agent can synthesize into patient-specific plans, handoffs, and outreach drafts.
- **Potential Impact**: transitions of care, medication reconciliation, and care gaps are high-cost, high-volume clinical workflow pain points.
- **Feasibility**: the server uses FHIR R4, SMART scopes, Prompt Opinion's MCP extension, de-identified/synthetic data only, and clear clinician-review guardrails.

## Tools

| MCP Tool | Purpose |
| --- | --- |
| `GenerateTransitionOfCareBrief` | Summarizes recent encounters, conditions, meds, allergies, labs, follow-up status, and risk drivers. |
| `FindLongitudinalCareGaps` | Finds diabetes, hypertension, CKD, and preventive care gaps from accessible FHIR resources. |
| `BuildMedicationSafetyBrief` | Flags high-risk meds, possible allergy conflicts, renal/potassium concerns, and risky combinations. |
| `DraftPatientOutreach` | Creates a clinician-review outreach script grounded in the patient-specific brief and gaps. |
| `CreatePostDischargeRescuePlan` | Builds a 0-24h, 24-48h, and 48-72h transition workflow with cited escalation triggers. |
| `GenerateTransitionTaskBundle` | Produces draft FHIR Task and CommunicationRequest resources for clinician review before write-back. |
| `PrioritizeTransitionPanel` | Ranks a small post-acute patient panel for care-manager triage. |

## Local Setup

Use Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run with synthetic FHIR fixtures:

```bash
export CAREBRIDGE_SYNTHETIC_FHIR=true
uvicorn carebridge_sentinel.main:app --host 0.0.0.0 --port 8000 --reload
```

Test the MCP endpoint:

```bash
curl -i http://localhost:8000/mcp
```

Run the automated end-to-end smoke test:

```bash
python scripts/e2e_mcp_smoke.py
```

Run the full local quality gate:

```bash
pytest -q
python scripts/phi_scan.py
python scripts/e2e_mcp_smoke.py
```

Production hardening options:

```bash
# Keep false in production unless you intentionally want fixture mode.
export CAREBRIDGE_SYNTHETIC_FHIR=false

# Optional: restrict accepted FHIR server hosts.
export CAREBRIDGE_ALLOWED_FHIR_HOSTS=app.promptopinion.ai

# Optional only for local private FHIR testing.
export CAREBRIDGE_ALLOW_INSECURE_FHIR=true
```

## Prompt Opinion Marketplace Setup

1. Deploy this server to a public HTTPS endpoint.
2. In Prompt Opinion, go to `Configuration -> MCP Servers`.
3. Add the MCP endpoint URL, for example `https://your-domain.example/mcp`.
4. Click `Continue` so Prompt Opinion sends `initialize`.
5. Confirm the FHIR context extension and authorize the requested SMART scopes.
6. Publish the server to the Prompt Opinion Marketplace.
7. Demo a Prompt Opinion agent invoking the tools inside the platform.

The server advertises this MCP capability extension:

```json
{
  "ai.promptopinion/fhir-context": {
    "scopes": [
      { "name": "patient/Patient.rs", "required": true },
      { "name": "patient/Encounter.rs" },
      { "name": "patient/Condition.rs" },
      { "name": "patient/Observation.rs" },
      { "name": "patient/MedicationRequest.rs" },
      { "name": "patient/MedicationStatement.rs" },
      { "name": "patient/AllergyIntolerance.rs" },
      { "name": "patient/Appointment.rs" },
      { "name": "patient/CarePlan.rs" },
      { "name": "patient/ServiceRequest.rs" },
      { "name": "patient/Procedure.rs" },
      { "name": "patient/Immunization.rs" }
    ]
  }
}
```

## Safety Model

- Do not send real PHI in local demo mode.
- The server does not persist FHIR tokens, patient IDs, or patient records.
- Tool outputs are decision-support drafts and include clinician-review language.
- Optional FHIR searches fail soft, so missing scopes do not crash the whole workflow.
- CI runs unit tests, a PHI/token scan, and an end-to-end MCP smoke test.

## Submission Assets

Use the files in `submission/` for your Devpost copy, marketplace positioning, and under-three-minute video script.
