import json
from pathlib import Path

from carebridge_sentinel.clinical import (
    build_snapshot,
    care_gap_findings,
    medication_findings,
    post_discharge_rescue_plan,
    risk_tier,
    transition_task_bundle,
    transition_findings,
)


def _record(patient_id="synthetic-patient-001"):
    bundle = json.loads(Path("examples/synthetic_patient_bundle.json").read_text())
    record = {"_errors": [], "_lookbackDays": 45}
    for entry in bundle["entry"]:
        resource = entry["resource"]
        if _belongs_to_patient(resource, patient_id):
            record.setdefault(resource["resourceType"], []).append(resource)
    for resource_type in [
        "Encounter",
        "Condition",
        "Observation",
        "MedicationRequest",
        "MedicationStatement",
        "AllergyIntolerance",
        "Appointment",
        "CarePlan",
        "ServiceRequest",
        "Procedure",
        "Immunization",
    ]:
        record.setdefault(resource_type, [])
    return record


def _belongs_to_patient(resource, patient_id):
    if resource["resourceType"] == "Patient":
        return resource.get("id") == patient_id
    expected = f"Patient/{patient_id}"
    if (resource.get("patient") or {}).get("reference") == expected:
        return True
    if (resource.get("subject") or {}).get("reference") == expected:
        return True
    for participant in resource.get("participant") or []:
        if (participant.get("actor") or {}).get("reference") == expected:
            return True
    return False


def test_transition_brief_detects_high_risk_synthetic_case():
    snapshot = build_snapshot(_record())
    findings = transition_findings(snapshot)
    tier, score = risk_tier(findings)

    assert tier == "High"
    assert score >= 9
    assert any("Recent acute-care encounter" == finding.title for finding in findings)
    assert any("No near-term follow-up found" == finding.title for finding in findings)


def test_medication_safety_detects_bleeding_and_potassium_signals():
    snapshot = build_snapshot(_record())
    findings = medication_findings(snapshot)
    titles = {finding.title for finding in findings}

    assert "Bleeding-risk medication combination" in titles
    assert "Potassium-sensitive medication context" in titles


def test_care_gaps_detect_diabetes_and_blood_pressure_context():
    snapshot = build_snapshot(_record())
    gaps = care_gap_findings(snapshot)
    titles = {finding.title for finding in gaps}

    assert "Elevated A1c" in titles
    assert "Elevated recent blood pressure" in titles


def test_post_discharge_rescue_plan_has_timeline_and_safety_note():
    plan = post_discharge_rescue_plan(_record())

    assert "0-24 Hours" in plan
    assert "24-48 Hours" in plan
    assert "48-72 Hours" in plan
    assert "synthetic-patient-001" in plan
    assert "Medication access barrier documented" in plan
    assert "Transportation barrier documented" in plan
    assert "Safety note:" in plan


def test_transition_task_bundle_generates_fhir_tasks_and_communication_request():
    bundle_text = transition_task_bundle(_record())

    assert '"resourceType": "Bundle"' in bundle_text
    assert '"resourceType": "Task"' in bundle_text
    assert '"resourceType": "CommunicationRequest"' in bundle_text
    assert '"priority": "urgent"' in bundle_text
    assert "clinician review before any write-back" in bundle_text


def test_lower_risk_patient_with_followup_is_not_ranked_high():
    snapshot = build_snapshot(_record("synthetic-patient-003"))
    findings = transition_findings(snapshot)
    tier, score = risk_tier(findings)

    assert tier == "Low"
    assert score < 4
    assert not any("No near-term follow-up found" == finding.title for finding in findings)
