# Under-Three-Minute Demo Script

## 0:00-0:20 - Problem

"After an ED visit or discharge, care teams have minutes to answer: what changed, what is risky, what follow-up is missing, and what should we tell the patient? That context is scattered across FHIR resources. CareBridge Sentinel gives Prompt Opinion agents a reusable transitions-of-care superpower."

## 0:20-0:45 - Marketplace and Protocol Gate

Show the MCP server configured in Prompt Opinion.

"This is published as an MCP server in the Prompt Opinion Marketplace. On initialize, it advertises the `ai.promptopinion/fhir-context` extension and SMART scopes, so Prompt Opinion can pass only the authorized patient context."

## 0:45-1:30 - Transition Brief

Ask the Prompt Opinion agent:

"Use CareBridge Sentinel to prioritize the post-discharge panel, then create a 72-hour rescue plan for the highest-risk patient."

Show the agent invoking `PrioritizeTransitionPanel`.

Call out:

- multiple synthetic patients
- ranked transition risk
- why the highest-risk patient should be first

Then ask:

"Use CareBridge Sentinel to create a 72-hour post-discharge rescue plan for the current patient. Prioritize the top three risks and actions."

Show the agent invoking `CreatePostDischargeRescuePlan`, then optionally `GenerateTransitionOfCareBrief`.

Call out:

- recent ED/inpatient encounter
- no follow-up within 14 days if present
- medication safety issue
- abnormal lab or chronic-condition driver
- cited FHIR evidence IDs
- 0-24h, 24-48h, and 48-72h action windows

## 1:30-2:05 - Medication Safety and Care Gaps

Ask:

"Now check medication safety and longitudinal care gaps."

Show `BuildMedicationSafetyBrief` and `FindLongitudinalCareGaps`.

Call out:

- anticoagulant plus NSAID signal
- potassium/eGFR context
- A1c or BP gap
- clinician-review guardrail

## 2:05-2:35 - Patient Outreach

Ask:

"Generate a draft FHIR transition task bundle, then draft a phone outreach script for clinician review using only the cited findings."

Show `GenerateTransitionTaskBundle`, then `DraftPatientOutreach`.

Call out that task creation and outreach are drafts for clinician review, grounded in FHIR facts, and not sent automatically.

## 2:35-2:55 - Why It Wins

"The AI factor is the conversion of fragmented clinical context into a concise, cited care-team artifact. The impact is reducing avoidable readmissions, missed follow-up, and medication confusion. The feasibility is real: FHIR R4, SHARP-on-MCP, no PHI persistence, authorized SMART scopes, and direct Prompt Opinion invocation."

## 2:55-3:00 - Close

"CareBridge Sentinel helps healthcare agents assemble the last mile of care."
