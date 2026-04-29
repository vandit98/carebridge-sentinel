FHIR_CONTEXT_EXTENSION = "ai.promptopinion/fhir-context"

FHIR_SERVER_URL_HEADER = "X-FHIR-Server-URL"
FHIR_ACCESS_TOKEN_HEADER = "X-FHIR-Access-Token"
PATIENT_ID_HEADER = "X-Patient-ID"
FHIR_REFRESH_TOKEN_HEADER = "X-FHIR-Refresh-Token"
FHIR_REFRESH_URL_HEADER = "X-FHIR-Refresh-Url"

FHIR_SCOPES = [
    {"name": "patient/Patient.rs", "required": True},
    {"name": "patient/Encounter.rs"},
    {"name": "patient/Condition.rs"},
    {"name": "patient/Observation.rs"},
    {"name": "patient/MedicationRequest.rs"},
    {"name": "patient/MedicationStatement.rs"},
    {"name": "patient/AllergyIntolerance.rs"},
    {"name": "patient/Appointment.rs"},
    {"name": "patient/CarePlan.rs"},
    {"name": "patient/ServiceRequest.rs"},
    {"name": "patient/Procedure.rs"},
    {"name": "patient/Immunization.rs"},
    {"name": "patient/DocumentReference.rs"},
]

SAFETY_NOTE = (
    "Clinical decision support draft only. Verify against the chart, local policy, "
    "and clinician judgment before acting."
)
