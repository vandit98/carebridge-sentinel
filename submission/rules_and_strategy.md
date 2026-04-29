# Hackathon Rules and Winning Strategy

Source pages checked on April 29, 2026:

- https://agents-assemble.devpost.com/
- https://agents-assemble.devpost.com/rules
- https://docs.promptopinion.ai/fhir-context/mcp-fhir-context
- https://www.sharponmcp.com/overview.html

## Key Dates

- Submission period: March 2, 2026 at 9:00 AM Eastern Time through May 11, 2026 at 11:00 PM Eastern Time.
- Judging period: May 11, 2026 at 10:00 AM Eastern Time through May 25, 2026 at 11:00 PM Eastern Time.
- Winners announced: around May 27, 2026 at 11:00 AM Eastern Time.

## Required Submission Gates

The project must:

- Develop a healthcare AI solution.
- Integrate into the Prompt Opinion multi-agent platform.
- Use one of the two accepted technical paths:
  - Path A: MCP server exposing specialized healthcare tools.
  - Path B: A2A-enabled agent.
- Be published to the Prompt Opinion Marketplace.
- Be discoverable and directly invokable inside Prompt Opinion.
- Function exactly as shown in the demo video.
- Use only synthetic or de-identified data. Real PHI is disqualifying.
- Include a text description, Marketplace URL, and public demo video.
- Keep the video under three minutes; judges are not required to watch beyond three minutes.

## Stage One: Pass/Fail

Before scoring, the submission must pass technical validation:

- Marketplace verified.
- Explicit MCP or A2A protocol adherence.
- Prompt Opinion platform integration and invocation.
- Safety compliance with no PHI.

This is why CareBridge Sentinel is built as an MCP server with Prompt Opinion's FHIR context extension, Docker deployment, a health check, and a marketplace checklist.

## Stage Two: Equally Weighted Scoring

### The AI Factor

Judge question: does the solution use generative AI for a problem traditional rules cannot solve?

CareBridge strategy:

- MCP tools extract, normalize, prioritize, and cite FHIR facts.
- A Prompt Opinion generative agent turns those facts into concise handoffs, outreach drafts, and next-best-action plans.
- A panel tool lets the agent reason across multiple post-acute patients before drilling into the highest-risk case.
- A FHIR task-bundle tool lets the agent move from explanation to a clinician-reviewable operational artifact.
- The demo should clearly show the agent transforming the MCP output into a polished clinical workflow artifact.

### Potential Impact

Judge question: does this solve a real pain point and improve outcomes, costs, or time?

CareBridge strategy:

- Focus on transitions of care, medication reconciliation, missed follow-up, and care gaps.
- Position the outcome hypothesis around reduced avoidable readmissions, fewer missed follow-ups, faster chart review, and safer medication handoff.
- In the video, say the pain point in the first 20 seconds.

### Feasibility

Judge question: could this exist in a real healthcare system today, with privacy, safety, and regulatory constraints respected?

CareBridge strategy:

- Use FHIR R4 and SMART scopes.
- Read FHIR context only from Prompt Opinion headers.
- Store no PHI, tokens, or patient IDs.
- Use synthetic/de-identified demo data.
- Mark all outputs as clinician-review decision support.
- Fail soft if optional FHIR resources are unavailable.
- Run unit tests, PHI/token scan, and MCP end-to-end smoke test before submission.

## Video Must Show

- The project inside Prompt Opinion, not only local code.
- Marketplace discovery or configuration.
- FHIR context authorization.
- At least one direct tool invocation.
- One clear AI-generated clinical artifact based on cited FHIR evidence.
- Safety guardrails and synthetic/de-identified data.
