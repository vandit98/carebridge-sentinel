# CareBridge Sentinel

CareBridge Sentinel is a FHIR-aware MCP superpower for Prompt Opinion that helps healthcare agents close the last-mile gap after acute care: medication reconciliation, follow-up routing, care-gap review, and patient outreach.

## What It Does

CareBridge Sentinel exposes four MCP tools:

- `GenerateTransitionOfCareBrief`: creates a cited transition-of-care risk brief from FHIR Patient, Encounter, Condition, Medication, Allergy, Observation, Appointment, CarePlan, ServiceRequest, Procedure, and Immunization resources.
- `FindLongitudinalCareGaps`: identifies diabetes, hypertension, CKD, and preventive-care gaps from accessible FHIR data.
- `BuildMedicationSafetyBrief`: flags high-risk meds, risky combinations, allergy-medication concerns, renal dosing context, and potassium-sensitive medication context.
- `DraftPatientOutreach`: drafts a clinician-review phone, portal, or SMS outreach message grounded in patient-specific evidence.
- `CreatePostDischargeRescuePlan`: builds a 0-24h, 24-48h, and 48-72h transition workflow with cited escalation triggers.
- `GenerateTransitionTaskBundle`: produces draft FHIR Task and CommunicationRequest resources for clinician review before write-back.
- `PrioritizeTransitionPanel`: ranks a small post-acute patient panel so care managers know who needs attention first.

## Why It Matters

Transitions of care are a painful operational bottleneck. Teams must review scattered chart facts, reconcile medications, confirm follow-up, and contact patients quickly. Missed follow-up, medication confusion, and unresolved care gaps drive avoidable readmissions, clinician burden, and patient harm.

CareBridge Sentinel gives any Prompt Opinion agent a reusable clinical safety superpower. The agent can invoke the MCP server, receive structured and cited FHIR evidence, triage a small transition panel, and produce a concise handoff, next-best-action plan, FHIR task bundle, and outreach draft for clinician review.

## How It Uses AI

The MCP server turns raw FHIR resources into structured, machine-readable clinical evidence. A Prompt Opinion generative agent uses that evidence to synthesize patient-specific plans, outreach language, and care-team summaries. This solves a problem traditional rules alone cannot: converting fragmented patient context into a useful, concise, explainable workflow artifact.

## Feasibility and Safety

- Supports Prompt Opinion's `ai.promptopinion/fhir-context` MCP extension.
- Requests SMART scopes explicitly and reads FHIR context from secure request headers.
- Uses no real PHI in development; local demo mode uses synthetic/de-identified fixtures only.
- Does not persist patient records, tokens, or patient IDs.
- Fails soft when optional FHIR scopes are unavailable.
- Every output is marked as clinician-review decision support.
- Includes a PHI/token scan, FHIR URL hardening, and end-to-end MCP smoke tests.

## Built With

Python, FastAPI, FastMCP, FHIR R4, SHARP-on-MCP, Prompt Opinion FHIR context, and synthetic FHIR demo fixtures.
