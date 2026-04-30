# MeDo Custom Plugin Spec

Use this if you want the MeDo app to invoke the live CareBridge Sentinel backend through MeDo's Custom Plugin system.

MeDo docs say custom plugins are created from **Plugins > Create Plugin** by pasting detailed API documentation, then clicking **AI Parse**, reviewing the generated plugin, and clicking **Create**.

Official docs: https://intl.cloud.baidu.com/en/doc/MIAODA/s/custom-plugin-en

## Plugin Information

Plugin Name: CareBridge Sentinel Clinical Safety API

Plugin Description:
CareBridge Sentinel provides synthetic-demo clinical safety APIs for transition-of-care review, medication safety, longitudinal care gaps, patient outreach, task bundle drafting, and panel prioritization. Outputs are clinician-review decision support and do not store PHI.

Authentication Method:
No authentication is required for the public synthetic demo endpoints.

Base URL:

```text
https://carebridge-sentinel.onrender.com
```

OpenAPI URL:

```text
https://carebridge-sentinel.onrender.com/openapi.json
```

Health Check:

```text
GET https://carebridge-sentinel.onrender.com/api/plugin/health
```

Success Response:

```json
{
  "status": "ok",
  "service": "carebridge-sentinel-plugin-api",
  "mcpEndpoint": "/mcp",
  "openApi": "/openapi.json"
}
```

## Endpoints

### 1. Prioritize Transition Panel

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/prioritize-transition-panel
```

Request Body:

```json
{
  "patientIds": "synthetic-patient-001,synthetic-patient-002,synthetic-patient-003",
  "lookbackDays": 45,
  "maxPatients": 10
}
```

Parameters:

- patientIds: Optional comma-separated FHIR Patient.id values. In synthetic demo mode, omit this to use built-in synthetic patients.
- lookbackDays: Number of days of recent transition context to evaluate. Default 45.
- maxPatients: Maximum number of patients to rank. Default 10.

Success Response:

```json
{
  "result": "# Transition Risk Panel\\n...",
  "safetyNote": "Clinician-review decision support only. The public demo uses synthetic/de-identified data and does not store patient records, tokens, or PHI."
}
```

### 2. Generate Transition Brief

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/transition-brief
```

Request Body:

```json
{
  "patientId": "synthetic-patient-001",
  "lookbackDays": 45
}
```

Success Response:

```json
{
  "result": "# Transition of Care Brief\\n...",
  "safetyNote": "Clinician-review decision support only. The public demo uses synthetic/de-identified data and does not store patient records, tokens, or PHI."
}
```

### 3. Create 72-Hour Rescue Plan

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/rescue-plan
```

Request Body:

```json
{
  "patientId": "synthetic-patient-001",
  "lookbackDays": 45
}
```

### 4. Build Medication Safety Brief

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/medication-safety
```

Request Body:

```json
{
  "patientId": "synthetic-patient-001",
  "lookbackDays": 365
}
```

### 5. Find Longitudinal Care Gaps

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/care-gaps
```

Request Body:

```json
{
  "patientId": "synthetic-patient-001",
  "lookbackDays": 365
}
```

### 6. Draft Patient Outreach

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/patient-outreach
```

Request Body:

```json
{
  "patientId": "synthetic-patient-001",
  "channel": "phone",
  "lookbackDays": 45
}
```

Parameters:

- channel: phone, portal, or sms.

### 7. Generate Transition Task Bundle

Request Method: POST

Full Request URL:

```text
https://carebridge-sentinel.onrender.com/api/plugin/task-bundle
```

Request Body:

```json
{
  "patientId": "synthetic-patient-001",
  "lookbackDays": 45
}
```

## Error Codes

- 422: Invalid request body or parameter range.
- 500: Server error or unavailable synthetic/FHIR context.

## Prompt To Use In A MeDo App After Creating The Plugin

```text
Use the @CareBridge Sentinel Clinical Safety API plugin to create a healthcare transition-of-care dashboard.

The app should let a user:
- Rank a synthetic post-discharge patient panel
- Select a patient
- Generate a transition-of-care brief
- Generate a 72-hour rescue plan
- Review medication safety
- Review longitudinal care gaps
- Draft patient outreach
- Generate a draft FHIR task bundle

Show all plugin outputs with clear clinician-review guardrails. Make it obvious that the public demo uses synthetic/de-identified data and does not store PHI.
```

