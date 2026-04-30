# CareBridge Sentinel Video Recording Script

Goal: record a clear demo under 3 minutes. Aim for 2:30-2:50 so Devpost judges see the whole story.

## Video Title

```text
CareBridge Sentinel - Prompt Opinion MCP Demo
```

## Links To Open Before Recording

GitHub repo:

```text
https://github.com/vandit98/carebridge-sentinel
```

Live health check:

```text
https://carebridge-sentinel.onrender.com/healthz
```

Prompt Opinion MCP server URL:

```text
https://carebridge-sentinel.onrender.com/mcp
```

Use `/healthz` in the browser. Use `/mcp` only inside Prompt Opinion or MCP curl commands.

## Best Demo Flow

Use this if Prompt Opinion is configured and can invoke the MCP server.

### 0:00-0:20 - Problem

Say:

```text
CareBridge Sentinel is a FHIR-aware MCP server for the first 72 hours after discharge.

After an ED visit or hospitalization, care teams need to know who needs outreach first, what medication risks changed, whether follow-up is booked, and whether barriers are hidden in notes.
```

### 0:20-0:40 - Live Endpoint

Show:

```text
https://carebridge-sentinel.onrender.com/healthz
```

Say:

```text
This is deployed live on Render. The MCP endpoint is available at /mcp and is configured for Prompt Opinion.
```

### 0:40-1:25 - Panel Triage

In Prompt Opinion, ask:

```text
Use CareBridge Sentinel to prioritize the post-discharge panel. Then create a 72-hour rescue plan for the highest-risk patient.
```

Point out:

```text
The tool ranks a synthetic post-discharge panel and identifies the highest-risk patients first. The ranking is based on cited FHIR evidence like recent encounters, abnormal labs, medication risk, missing follow-up, and barriers from notes.
```

### 1:25-2:10 - 72-Hour Rescue Plan

Show the rescue plan output.

Say:

```text
The output is organized into 0-24 hour, 24-48 hour, and 48-72 hour actions. This makes it useful for care managers instead of being just another clinical summary.
```

Point out:

```text
- Follow-up closure
- Medication safety
- Barrier detection
- Cited FHIR evidence
- Clinician-review guardrails
```

### 2:10-2:40 - FHIR Task Bundle And Outreach

In Prompt Opinion, ask:

```text
Generate a draft FHIR transition task bundle and a phone outreach draft for clinician review.
```

Say:

```text
CareBridge can generate draft FHIR Task and CommunicationRequest resources. It does not auto-send anything or make autonomous clinical decisions. Everything is for clinician review.
```

### 2:40-2:55 - Close

Say:

```text
The AI factor is that Prompt Opinion can turn these MCP outputs into patient-specific care-manager workflows.

The impact is reducing missed follow-up, medication confusion, and avoidable post-discharge harm.

The feasibility is real: FHIR R4, MCP, synthetic data, no PHI storage, and clinician-review guardrails.
```

## Backup Demo Flow

Use this only if Prompt Opinion setup is not ready. The Prompt Opinion demo is better for judging.

### Show Tool List

```bash
curl -N -X POST https://carebridge-sentinel.onrender.com/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Run Panel Triage

```bash
curl -N -X POST https://carebridge-sentinel.onrender.com/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"PrioritizeTransitionPanel","arguments":{"lookbackDays":45,"maxPatients":10}}}'
```

### Run 72-Hour Rescue Plan

```bash
curl -N -X POST https://carebridge-sentinel.onrender.com/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"CreatePostDischargeRescuePlan","arguments":{"patientId":"synthetic-patient-001","lookbackDays":45}}}'
```

### Run FHIR Task Bundle

```bash
curl -N -X POST https://carebridge-sentinel.onrender.com/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"GenerateTransitionTaskBundle","arguments":{"patientId":"synthetic-patient-001","lookbackDays":45}}}'
```

## Recording Tips

- Use QuickTime Player -> File -> New Screen Recording.
- Keep browser zoom around 90-100%.
- Do not show private API keys, tokens, or account settings.
- Start with the Render `/healthz` page so viewers know it is live.
- Spend most of the time in Prompt Opinion if possible.
- Stop recording before 3 minutes.
- Upload to YouTube as Unlisted.
- Paste the YouTube URL into Devpost's Video Demo Link field.

## Devpost Video Link

After uploading to YouTube, paste the final unlisted URL here:

```text
PASTE_YOUTUBE_URL_HERE
```
