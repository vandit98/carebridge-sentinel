from __future__ import annotations

import json
import re
import base64
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from carebridge_sentinel.constants import SAFETY_NOTE


@dataclass(frozen=True)
class Finding:
    severity: str
    title: str
    detail: str
    evidence: list[str]
    action: str


def transition_brief(record: dict[str, Any]) -> str:
    snapshot = build_snapshot(record)
    findings = transition_findings(snapshot)
    tier, score = risk_tier(findings)

    sections = [
        "# CareBridge Transition-of-Care Brief",
        f"**Patient:** {snapshot['patientLabel']}",
        f"**Risk tier:** {tier} (score {score})",
        "",
        "## One-Minute Clinical Hypothesis",
        _clinical_hypothesis(snapshot, findings),
        "",
        "## Priority Drivers",
        _format_findings(findings[:6]),
        "",
        "## Suggested Next Actions",
        _format_actions(findings[:6]),
        "",
        "## Context Snapshot",
        _format_context_snapshot(snapshot),
        "",
        "## Agent Handoff JSON",
        "```json",
        json.dumps(
            {
                "patient": snapshot["patientLabel"],
                "riskTier": tier,
                "riskScore": score,
                "topFindings": [finding.__dict__ for finding in findings[:6]],
                "safetyNote": SAFETY_NOTE,
            },
            indent=2,
        ),
        "```",
        "",
        f"**Safety note:** {SAFETY_NOTE}",
    ]
    return "\n".join(sections)


def care_gap_brief(record: dict[str, Any]) -> str:
    snapshot = build_snapshot(record)
    gaps = care_gap_findings(snapshot)
    sections = [
        "# Longitudinal Care-Gap Review",
        f"**Patient:** {snapshot['patientLabel']}",
        "",
        "## Gaps To Review",
        _format_findings(gaps) if gaps else "No major rule-based care gaps were detected in accessible FHIR data.",
        "",
        "## Recommended Agent Behavior",
        (
            "Use these gaps as cited evidence for a concise clinician-facing plan. "
            "Do not imply a diagnosis or overdue service unless the accessible FHIR record supports it."
        ),
        "",
        "## Machine-Readable Gaps",
        "```json",
        json.dumps([gap.__dict__ for gap in gaps], indent=2),
        "```",
        "",
        f"**Safety note:** {SAFETY_NOTE}",
    ]
    return "\n".join(sections)


def medication_safety_brief(record: dict[str, Any]) -> str:
    snapshot = build_snapshot(record)
    findings = medication_findings(snapshot)
    sections = [
        "# Medication Safety Brief",
        f"**Patient:** {snapshot['patientLabel']}",
        "",
        "## Safety Signals",
        _format_findings(findings) if findings else "No high-priority medication safety signals were detected.",
        "",
        "## Active Medication Names",
        _bullet(snapshot["medicationNames"]) if snapshot["medicationNames"] else "No active medication resources were accessible.",
        "",
        "## Allergy Names",
        _bullet(snapshot["allergyNames"]) if snapshot["allergyNames"] else "No allergy resources were accessible.",
        "",
        f"**Safety note:** {SAFETY_NOTE}",
    ]
    return "\n".join(sections)


def outreach_draft(record: dict[str, Any], channel: str) -> str:
    snapshot = build_snapshot(record)
    findings = transition_findings(snapshot)[:3]
    gaps = care_gap_findings(snapshot)[:3]

    if channel.lower() not in {"phone", "portal", "sms"}:
        channel = "phone"

    if channel.lower() == "sms":
        body = (
            f"Hello, this is your care team. We would like to check in after your recent care "
            f"and confirm follow-up, medications, and any new symptoms. Please reply or call us. "
            f"If symptoms feel urgent, seek emergency care."
        )
    elif channel.lower() == "portal":
        body = (
            "Hello,\n\n"
            "We are checking in after your recent care. Please confirm whether you have your follow-up appointment, "
            "whether you were able to obtain and understand your medications, and whether you have any worsening symptoms. "
            "A clinician may review your chart for the items below and follow up with you.\n"
        )
    else:
        body = (
            "Hello, this is the care team calling to check in after your recent care. "
            "I want to confirm three things: that you have follow-up scheduled, that your medicines make sense, "
            "and that you know what symptoms should prompt urgent help."
        )

    sections = [
        "# Patient Outreach Draft",
        f"**Patient:** {snapshot['patientLabel']}",
        f"**Channel:** {channel.lower()}",
        "",
        "## Draft Message",
        body,
        "",
        "## Clinician Checklist Before Sending",
        _format_actions(findings + gaps) if findings or gaps else "- Confirm no urgent chart issues were missed.",
        "",
        "## Evidence Used",
        _format_findings(findings + gaps) if findings or gaps else "No priority evidence available.",
        "",
        f"**Safety note:** {SAFETY_NOTE}",
    ]
    return "\n".join(sections)


def post_discharge_rescue_plan(record: dict[str, Any]) -> str:
    snapshot = build_snapshot(record)
    findings = transition_findings(snapshot)
    gaps = care_gap_findings(snapshot)
    medication_signals = medication_findings(snapshot)
    document_signals = _document_risk_findings(snapshot)
    tier, score = risk_tier(findings)

    first_day = findings[:3]
    second_day = medication_signals[:3]
    third_day = gaps[:3]

    sections = [
        "# 72-Hour Post-Discharge Rescue Plan",
        f"**Patient:** {snapshot['patientLabel']}",
        f"**Transition risk:** {tier} (score {score})",
        "",
        "## Agent Goal",
        (
            "Convert fragmented FHIR context into a short, auditable recovery workflow: "
            "verify safety today, close medication/follow-up loops tomorrow, and schedule longitudinal gap closure by hour 72."
        ),
        "",
        "## 0-24 Hours: Safety Verification",
        _format_timeline(first_day, "Confirm the patient is clinically stable and understands urgent-return precautions."),
        "",
        "## 24-48 Hours: Medication and Follow-Up Loop Closure",
        _format_timeline(second_day, "Complete medication reconciliation and confirm the next appointment or escalation path."),
        "",
        "## Transition Barriers From Notes",
        _format_findings(document_signals) if document_signals else "No unstructured transition-barrier notes were available.",
        "",
        "## 48-72 Hours: Longitudinal Gap Closure",
        _format_timeline(third_day, "Queue lower-urgency chronic care and preventive gaps without distracting from transition safety."),
        "",
        "## Escalation Triggers For Clinician Review",
        _format_escalation_triggers(findings + medication_signals),
        "",
        "## Evidence Packet For Prompt Opinion Agent",
        "```json",
        json.dumps(
            {
                "patient": snapshot["patientLabel"],
                "transitionRiskTier": tier,
                "transitionRiskScore": score,
                "first24Hours": [finding.__dict__ for finding in first_day],
                "next48Hours": [finding.__dict__ for finding in second_day],
                "by72Hours": [finding.__dict__ for finding in third_day],
                "agentInstruction": (
                    "Use this packet to produce a concise care-manager plan. "
                    "Cite evidence IDs. Do not diagnose, prescribe, or claim tasks are complete."
                ),
                "safetyNote": SAFETY_NOTE,
            },
            indent=2,
        ),
        "```",
        "",
        f"**Safety note:** {SAFETY_NOTE}",
    ]
    return "\n".join(sections)


def transition_task_bundle(record: dict[str, Any]) -> str:
    snapshot = build_snapshot(record)
    findings = transition_findings(snapshot)[:8]
    tier, score = risk_tier(findings)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    patient_reference = f"Patient/{snapshot['patient'].get('id', 'unknown')}"

    entries: list[dict[str, Any]] = []
    for index, finding in enumerate(findings, start=1):
        task_id = f"carebridge-task-{index}"
        entries.append(
            {
                "fullUrl": f"urn:uuid:{task_id}",
                "resource": {
                    "resourceType": "Task",
                    "id": task_id,
                    "status": "requested",
                    "intent": "order",
                    "priority": _task_priority(finding.severity),
                    "code": {"text": finding.title},
                    "description": finding.action,
                    "for": {"reference": patient_reference},
                    "authoredOn": now,
                    "note": [
                        {
                            "text": (
                                f"{finding.detail} Evidence: "
                                f"{', '.join(finding.evidence) if finding.evidence else 'no direct resource reference'}"
                            )
                        }
                    ],
                },
            }
        )

    entries.append(
        {
            "fullUrl": "urn:uuid:carebridge-communicationrequest",
            "resource": {
                "resourceType": "CommunicationRequest",
                "id": "carebridge-communicationrequest",
                "status": "draft",
                "priority": "urgent" if tier == "High" else "routine",
                "subject": {"reference": patient_reference},
                "authoredOn": now,
                "payload": [
                    {
                        "contentString": (
                            "CareBridge Sentinel recommends clinician-reviewed outreach within the "
                            "72-hour transition window. Confirm follow-up, medication access, warning signs, "
                            "and patient barriers before sending."
                        )
                    }
                ],
            },
        }
    )

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": now,
        "entry": entries,
        "extension": [
            {
                "url": "https://carebridge-sentinel.local/fhir/StructureDefinition/transition-risk",
                "valueString": f"{tier} ({score})",
            }
        ],
    }

    sections = [
        "# FHIR Transition Action Bundle",
        f"**Patient:** {snapshot['patientLabel']}",
        f"**Transition risk:** {tier} (score {score})",
        "",
        "This draft bundle is intended for clinician review before any write-back or task creation.",
        "",
        "```json",
        json.dumps(bundle, indent=2),
        "```",
        "",
        f"**Safety note:** {SAFETY_NOTE}",
    ]
    return "\n".join(sections)


def panel_transition_summary(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: row["riskScore"], reverse=True)
    sections = [
        "# Transition Risk Panel",
        "Care-manager queue for post-acute outreach. Highest-risk patients appear first.",
        "",
        "## Ranked Queue",
    ]

    for index, row in enumerate(ordered, start=1):
        drivers = "; ".join(row["topDrivers"]) if row["topDrivers"] else "No major drivers detected"
        sections.append(
            f"{index}. **{row['riskTier']} ({row['riskScore']}) - {row['patientLabel']}**: {drivers}"
        )

    sections.extend(
        [
            "",
            "## Suggested Queue Actions",
            "- Start with High-risk patients who have no near-term follow-up or medication safety signals.",
            "- Use `CreatePostDischargeRescuePlan` for the highest-risk patient before drafting outreach.",
            "- Use `GenerateTransitionTaskBundle` only after clinician review confirms task creation is appropriate.",
            "",
            "## Machine-Readable Panel",
            "```json",
            json.dumps(ordered, indent=2),
            "```",
            "",
            f"**Safety note:** {SAFETY_NOTE}",
        ]
    )
    return "\n".join(sections)


def build_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    patient = record["Patient"][0]
    conditions = [_condition_summary(item) for item in record.get("Condition", [])]
    encounters = [_encounter_summary(item) for item in record.get("Encounter", [])]
    observations = [_observation_summary(item) for item in record.get("Observation", [])]
    meds = [_medication_summary(item) for item in record.get("MedicationRequest", []) + record.get("MedicationStatement", [])]
    allergies = [_allergy_summary(item) for item in record.get("AllergyIntolerance", [])]
    appointments = [_appointment_summary(item) for item in record.get("Appointment", [])]
    procedures = [_procedure_summary(item) for item in record.get("Procedure", [])]
    immunizations = [_immunization_summary(item) for item in record.get("Immunization", [])]
    documents = [_document_summary(item) for item in record.get("DocumentReference", [])]

    return {
        "patient": patient,
        "patientLabel": patient_label(patient),
        "age": patient_age(patient),
        "conditions": conditions,
        "encounters": sorted(encounters, key=lambda x: x.get("start") or date.min, reverse=True),
        "observations": sorted(observations, key=lambda x: x.get("effective") or date.min, reverse=True),
        "medications": meds,
        "medicationNames": sorted({item["name"] for item in meds if item.get("name")}),
        "allergies": allergies,
        "allergyNames": sorted({item["name"] for item in allergies if item.get("name")}),
        "appointments": sorted(appointments, key=lambda x: x.get("start") or date.max),
        "procedures": procedures,
        "immunizations": immunizations,
        "documents": documents,
        "errors": record.get("_errors", []),
    }


def transition_findings(snapshot: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    today = date.today()
    recent_encounters = [
        enc for enc in snapshot["encounters"]
        if enc.get("start") and enc["start"] >= today - timedelta(days=45)
    ]
    acute_encounters = [
        enc for enc in recent_encounters
        if any(term in enc["classText"].lower() for term in ["inpatient", "imp", "emergency", "er", "ed"])
    ]

    if acute_encounters:
        latest = acute_encounters[0]
        findings.append(
            Finding(
                "high",
                "Recent acute-care encounter",
                f"{latest['classText']} encounter on {_fmt_date(latest.get('start'))}: {latest['reason'] or 'reason not coded'}",
                [latest["reference"]],
                "Confirm discharge instructions, medication changes, and follow-up within 7-14 days.",
            )
        )

    if acute_encounters and not _has_near_followup(snapshot["appointments"], acute_encounters[0].get("end") or acute_encounters[0].get("start")):
        findings.append(
            Finding(
                "high",
                "No near-term follow-up found",
                "No booked appointment was found within 14 days after the most recent acute-care encounter.",
                [acute_encounters[0]["reference"]],
                "Route to scheduling or care management to close the follow-up loop.",
            )
        )

    findings.extend(medication_findings(snapshot)[:4])
    findings.extend(_lab_risk_findings(snapshot))
    findings.extend(_document_risk_findings(snapshot))

    chronic = _high_risk_conditions(snapshot["conditions"])
    if len(chronic) >= 2:
        findings.append(
            Finding(
                "medium",
                "Multiple chronic risk conditions",
                f"Active/problem-list conditions include {', '.join(chronic[:5])}.",
                [item["reference"] for item in snapshot["conditions"][:5]],
                "Keep the AI response focused on care coordination and avoid single-disease tunnel vision.",
            )
        )

    return _sort_findings(findings)


def medication_findings(snapshot: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    meds = [item for item in snapshot["medications"] if item.get("name")]
    med_names = [item["name"] for item in meds]
    med_blob = " | ".join(med_names).lower()

    high_risk = [name for name in med_names if _contains_any(name, HIGH_RISK_MED_TERMS)]
    if high_risk:
        findings.append(
            Finding(
                "medium",
                "High-risk medication review",
                f"Medication list includes {', '.join(high_risk[:6])}.",
                [item["reference"] for item in meds if item["name"] in high_risk][:6],
                "Ask the clinician-facing agent to verify dose, indication, renal adjustment, and recent changes.",
            )
        )

    if len(med_names) >= 8:
        findings.append(
            Finding(
                "medium",
                "Polypharmacy signal",
                f"{len(med_names)} active medication resources were found.",
                [item["reference"] for item in meds[:8]],
                "Prioritize reconciliation, adherence barriers, duplicate therapy, and deprescribing opportunities.",
            )
        )

    if _contains_any(med_blob, ["opioid", "oxycodone", "hydrocodone", "morphine", "tramadol"]) and _contains_any(
        med_blob,
        ["benzodiazepine", "alprazolam", "lorazepam", "diazepam", "clonazepam"],
    ):
        findings.append(
            Finding(
                "high",
                "Opioid and benzodiazepine combination",
                "The active medication list contains terms consistent with both opioid and benzodiazepine therapy.",
                [item["reference"] for item in meds if _contains_any(item["name"], ["oxycodone", "hydrocodone", "morphine", "tramadol", "alprazolam", "lorazepam", "diazepam", "clonazepam"])],
                "Flag for clinician review of sedation, respiratory risk, naloxone, and taper plan if appropriate.",
            )
        )

    if _contains_any(med_blob, ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "anticoagulant"]) and _contains_any(
        med_blob,
        ["ibuprofen", "naproxen", "nsaid", "aspirin"],
    ):
        findings.append(
            Finding(
                "high",
                "Bleeding-risk medication combination",
                "The medication list contains anticoagulant and NSAID/antiplatelet terms.",
                [item["reference"] for item in meds if _contains_any(item["name"], ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "ibuprofen", "naproxen", "aspirin"])],
                "Confirm indication, duration, bleeding history, and safer pain-control options.",
            )
        )

    for allergy in snapshot["allergies"]:
        allergy_terms = _meaningful_tokens(allergy["name"])
        if not allergy_terms:
            continue
        matched = [med for med in meds if any(term in med["name"].lower() for term in allergy_terms)]
        if matched:
            findings.append(
                Finding(
                    "high",
                    "Possible allergy-medication conflict",
                    f"Allergy '{allergy['name']}' appears related to active medication(s): {', '.join(item['name'] for item in matched)}.",
                    [allergy["reference"]] + [item["reference"] for item in matched],
                    "Do not treat this as proof of a true conflict; ask a clinician to verify allergy specificity and cross-reactivity.",
                )
            )

    latest_k = latest_observation(snapshot, "potassium")
    latest_egfr = latest_observation(snapshot, "egfr")
    if latest_k and latest_k.get("value") and latest_k["value"] >= 5.3 and _contains_any(med_blob, ["lisinopril", "losartan", "spironolactone", "potassium"]):
        findings.append(
            Finding(
                "high",
                "Potassium-sensitive medication context",
                f"Latest potassium is {latest_k['value']} {latest_k.get('unit') or ''}.",
                [latest_k["reference"]],
                "Review ACE/ARB/MRA/potassium therapy and repeat-lab plan.",
            )
        )

    if latest_egfr and latest_egfr.get("value") and latest_egfr["value"] < 45 and high_risk:
        findings.append(
            Finding(
                "medium",
                "Renal dosing review",
                f"Latest eGFR is {latest_egfr['value']} {latest_egfr.get('unit') or ''} with high-risk meds present.",
                [latest_egfr["reference"]],
                "Ask the clinician to verify renal dose adjustment and monitoring.",
            )
        )

    return _sort_findings(findings)


def care_gap_findings(snapshot: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    conditions_blob = " | ".join(item["name"].lower() for item in snapshot["conditions"])
    diabetes = "diabetes" in conditions_blob or latest_observation(snapshot, "a1c") is not None
    hypertension = "hypertension" in conditions_blob or latest_observation(snapshot, "systolic_bp") is not None
    ckd = any(term in conditions_blob for term in ["kidney", "ckd", "renal"]) or (
        (latest_observation(snapshot, "egfr") or {}).get("value") or 999
    ) < 60

    if diabetes:
        a1c = latest_observation(snapshot, "a1c")
        findings.extend(_freshness_gap("Hemoglobin A1c", a1c, 180, "high", "Review diabetes monitoring and treatment intensification if clinically appropriate."))
        if a1c and a1c.get("value") and a1c["value"] >= 8:
            findings.append(
                Finding(
                    "high" if a1c["value"] >= 9 else "medium",
                    "Elevated A1c",
                    f"Latest A1c is {a1c['value']}% on {_fmt_date(a1c.get('effective'))}.",
                    [a1c["reference"]],
                    "Queue clinician review for medication adherence, barriers, and treatment plan.",
                )
            )
        findings.extend(_freshness_gap("eGFR", latest_observation(snapshot, "egfr"), 365, "medium", "Confirm annual kidney monitoring for diabetes."))
        findings.extend(_freshness_gap("LDL cholesterol", latest_observation(snapshot, "ldl"), 365, "medium", "Confirm annual lipid monitoring."))
        findings.extend(_freshness_gap("Urine albumin", latest_observation(snapshot, "urine_albumin"), 365, "medium", "Confirm kidney damage screening."))

    if hypertension:
        systolic = latest_observation(snapshot, "systolic_bp")
        diastolic = latest_observation(snapshot, "diastolic_bp")
        bp_evidence = [item["reference"] for item in [systolic, diastolic] if item]
        if not systolic and not diastolic:
            findings.append(
                Finding(
                    "medium",
                    "No recent blood pressure found",
                    "No blood pressure observation was available in accessible FHIR data.",
                    [],
                    "Ask care team to capture a current BP or verify external readings.",
                )
            )
        elif (systolic and systolic.get("value", 0) >= 140) or (diastolic and diastolic.get("value", 0) >= 90):
            findings.append(
                Finding(
                    "medium",
                    "Elevated recent blood pressure",
                    f"Latest BP components include systolic={_obs_value(systolic)} and diastolic={_obs_value(diastolic)}.",
                    bp_evidence,
                    "Confirm home readings, adherence, symptoms, and follow-up plan.",
                )
            )

    if ckd:
        egfr = latest_observation(snapshot, "egfr")
        findings.extend(_freshness_gap("eGFR", egfr, 180, "high", "Confirm CKD monitoring cadence."))
        findings.extend(_freshness_gap("Potassium", latest_observation(snapshot, "potassium"), 180, "medium", "Confirm electrolyte monitoring."))
        if egfr and egfr.get("value") and egfr["value"] < 30:
            findings.append(
                Finding(
                    "high",
                    "Advanced CKD signal",
                    f"Latest eGFR is {egfr['value']} {egfr.get('unit') or ''}.",
                    [egfr["reference"]],
                    "Review nephrology involvement, medication dosing, and safety-net instructions.",
                )
            )

    age = snapshot.get("age")
    if age and age >= 65 and not _recent_immunization(snapshot["immunizations"], ["influenza", "flu"], 365):
        findings.append(
            Finding(
                "low",
                "Influenza immunization not found",
                "No influenza immunization was found in accessible FHIR data in the past year.",
                [],
                "Verify immunization history before recommending vaccination.",
            )
        )

    return _sort_findings(_dedupe_findings(findings))


def risk_tier(findings: list[Finding]) -> tuple[str, int]:
    score = sum({"high": 3, "medium": 2, "low": 1}.get(finding.severity, 1) for finding in findings)
    if score >= 9:
        return "High", score
    if score >= 4:
        return "Medium", score
    return "Low", score


def latest_observation(snapshot: dict[str, Any], label: str) -> dict[str, Any] | None:
    for observation in snapshot["observations"]:
        if observation.get("label") == label:
            return observation
    return None


def patient_label(patient: dict[str, Any]) -> str:
    names = patient.get("name") or []
    if names:
        first = names[0]
        given = " ".join(first.get("given") or [])
        family = first.get("family") or ""
        full_name = " ".join(part for part in [given, family] if part).strip()
        if full_name:
            return f"{full_name} ({patient.get('id', 'unknown id')})"
    return patient.get("id", "Unknown patient")


def patient_age(patient: dict[str, Any]) -> int | None:
    birth_date = _parse_date(patient.get("birthDate"))
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _condition_summary(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _code_display(resource.get("code")) or "Uncoded condition",
        "clinicalStatus": _code_display(resource.get("clinicalStatus")),
        "reference": _ref(resource),
    }


def _encounter_summary(resource: dict[str, Any]) -> dict[str, Any]:
    period = resource.get("period") or {}
    return {
        "classText": _encounter_class(resource),
        "reason": _first_display(resource.get("reasonCode")) or _first_display(resource.get("type")) or "",
        "start": _parse_date(period.get("start")),
        "end": _parse_date(period.get("end")),
        "reference": _ref(resource),
    }


def _observation_summary(resource: dict[str, Any]) -> dict[str, Any]:
    base = {
        "label": _observation_label(resource),
        "name": _code_display(resource.get("code")) or "Observation",
        "effective": _parse_date(resource.get("effectiveDateTime") or resource.get("issued")),
        "reference": _ref(resource),
    }
    value = resource.get("valueQuantity") or {}
    if value:
        base.update({"value": value.get("value"), "unit": value.get("unit") or value.get("code")})
    return base


def _medication_summary(resource: dict[str, Any]) -> dict[str, Any]:
    medication = (
        _code_display(resource.get("medicationCodeableConcept"))
        or (resource.get("medicationReference") or {}).get("display")
        or "Unnamed medication"
    )
    return {"name": medication, "status": resource.get("status"), "reference": _ref(resource)}


def _allergy_summary(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _code_display(resource.get("code")) or "Uncoded allergy",
        "criticality": resource.get("criticality"),
        "reference": _ref(resource),
    }


def _appointment_summary(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "description": resource.get("description") or _first_display(resource.get("serviceType")) or "Appointment",
        "status": resource.get("status"),
        "start": _parse_date(resource.get("start")),
        "reference": _ref(resource),
    }


def _procedure_summary(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _code_display(resource.get("code")) or "Procedure",
        "performed": _parse_date(resource.get("performedDateTime")),
        "reference": _ref(resource),
    }


def _immunization_summary(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _code_display(resource.get("vaccineCode")) or "Immunization",
        "occurrence": _parse_date(resource.get("occurrenceDateTime") or resource.get("occurrenceString")),
        "reference": _ref(resource),
    }


def _document_summary(resource: dict[str, Any]) -> dict[str, Any]:
    texts = []
    for content in resource.get("content") or []:
        attachment = content.get("attachment") or {}
        if attachment.get("data"):
            try:
                decoded = base64.b64decode(attachment["data"]).decode("utf-8", errors="ignore")
            except Exception:
                decoded = ""
            if decoded:
                texts.append(decoded)
        elif attachment.get("title"):
            texts.append(str(attachment["title"]))

    return {
        "name": _code_display(resource.get("type")) or resource.get("description") or "DocumentReference",
        "date": _parse_date(resource.get("date")),
        "text": "\n".join(texts)[:3000],
        "reference": _ref(resource),
    }


def _lab_risk_findings(snapshot: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    thresholds = [
        ("egfr", "Reduced eGFR", lambda value: value < 60, "Review renal dosing, nephrotoxin exposure, and repeat-lab plan."),
        ("potassium", "Abnormal potassium", lambda value: value < 3.5 or value > 5.2, "Review medication contributors and need for repeat testing."),
        ("hemoglobin", "Low hemoglobin", lambda value: value < 10, "Assess bleeding, anemia workup, and follow-up plan."),
        ("a1c", "Elevated A1c", lambda value: value >= 8, "Review diabetes plan and barriers."),
    ]
    for label, title, predicate, action in thresholds:
        obs = latest_observation(snapshot, label)
        if obs and obs.get("value") is not None and predicate(float(obs["value"])):
            findings.append(
                Finding(
                    "high" if label in {"potassium", "egfr"} else "medium",
                    title,
                    f"{obs['name']} is {obs['value']} {obs.get('unit') or ''} on {_fmt_date(obs.get('effective'))}.",
                    [obs["reference"]],
                    action,
                )
            )
    return findings


def _document_risk_findings(snapshot: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    docs = snapshot.get("documents") or []
    if not docs:
        return findings

    combined = "\n".join(doc.get("text", "") for doc in docs).lower()
    evidence = [doc["reference"] for doc in docs if doc.get("text")][:5]
    if not combined:
        return findings

    patterns = [
        (
            "high",
            "Medication access barrier documented",
            ["did not pick up", "unable to afford", "cost", "pharmacy barrier", "no refill"],
            "Ask care management or pharmacy to verify medication access before the patient leaves the 72-hour window.",
        ),
        (
            "medium",
            "Transportation barrier documented",
            ["transportation", "ride", "no car", "cannot get to appointment", "missed appointment due to ride"],
            "Route to scheduling/care management for transportation support and appointment confirmation.",
        ),
        (
            "medium",
            "Home support concern documented",
            ["lives alone", "limited support", "caregiver unavailable", "unsafe at home"],
            "Confirm home support, caregiver contact, and whether home health or social work review is needed.",
        ),
        (
            "medium",
            "Health literacy concern documented",
            ["confused about", "does not understand", "low literacy", "instructions unclear"],
            "Use plain-language teach-back during outreach and verify warning signs.",
        ),
    ]

    for severity, title, terms, action in patterns:
        if any(term in combined for term in terms):
            findings.append(
                Finding(
                    severity,
                    title,
                    "Unstructured transition documentation contains language consistent with this risk.",
                    evidence,
                    action,
                )
            )
    return findings


def _clinical_hypothesis(snapshot: dict[str, Any], findings: list[Finding]) -> str:
    if not findings:
        return "Accessible FHIR data did not surface urgent transition-of-care risks; use the agent to verify follow-up and medication understanding."
    top = findings[0]
    context = ", ".join(item["name"] for item in snapshot["conditions"][:3]) or "limited condition context"
    return (
        f"The chart suggests a transition risk centered on {top.title.lower()} in the setting of {context}. "
        "A generative agent should convert the cited findings into a concise care-team handoff, then ask a clinician to confirm before action."
    )


def _format_findings(findings: list[Finding]) -> str:
    lines = []
    for finding in findings:
        evidence = ", ".join(finding.evidence) if finding.evidence else "no direct resource reference"
        lines.append(f"- **[{finding.severity.upper()}] {finding.title}:** {finding.detail} Evidence: {evidence}.")
    return "\n".join(lines)


def _format_actions(findings: list[Finding]) -> str:
    seen = []
    for finding in findings:
        if finding.action not in seen:
            seen.append(finding.action)
    return "\n".join(f"- {action}" for action in seen) if seen else "- Continue routine review."


def _format_timeline(findings: list[Finding], fallback: str) -> str:
    if not findings:
        return f"- {fallback}"
    lines = []
    for finding in findings:
        evidence = ", ".join(finding.evidence) if finding.evidence else "no direct resource reference"
        lines.append(f"- **{finding.title}:** {finding.action} Evidence: {evidence}.")
    return "\n".join(lines)


def _format_escalation_triggers(findings: list[Finding]) -> str:
    high = [finding for finding in findings if finding.severity == "high"]
    if not high:
        return "- No high-severity escalation triggers were detected in accessible FHIR data."
    return "\n".join(f"- {finding.title}: {finding.detail}" for finding in high[:8])


def _task_priority(severity: str) -> str:
    return {"high": "urgent", "medium": "asap", "low": "routine"}.get(severity, "routine")


def _format_context_snapshot(snapshot: dict[str, Any]) -> str:
    lines = [
        f"- Age: {snapshot.get('age') if snapshot.get('age') is not None else 'unknown'}",
        f"- Recent encounters: {len(snapshot['encounters'])}",
        f"- Active/problem-list conditions: {', '.join(item['name'] for item in snapshot['conditions'][:8]) or 'none accessible'}",
        f"- Medication resources: {len(snapshot['medications'])}",
        f"- Allergy resources: {len(snapshot['allergies'])}",
    ]
    if snapshot["errors"]:
        lines.append(f"- Optional FHIR searches with errors: {'; '.join(snapshot['errors'])}")
    return "\n".join(lines)


def _freshness_gap(name: str, observation: dict[str, Any] | None, max_age_days: int, severity: str, action: str) -> list[Finding]:
    if not observation:
        return [
            Finding(
                severity,
                f"{name} not found",
                f"No {name} observation was found in accessible FHIR data.",
                [],
                action,
            )
        ]
    effective = observation.get("effective")
    if effective and effective < date.today() - timedelta(days=max_age_days):
        return [
            Finding(
                severity,
                f"{name} may be stale",
                f"Latest {name} is from {_fmt_date(effective)}.",
                [observation["reference"]],
                action,
            )
        ]
    return []


def _has_near_followup(appointments: list[dict[str, Any]], anchor: date | None) -> bool:
    if not anchor:
        anchor = date.today()
    window_end = anchor + timedelta(days=14)
    for appointment in appointments:
        start = appointment.get("start")
        if start and anchor <= start <= window_end and appointment.get("status") not in {"cancelled", "noshow"}:
            return True
    return False


def _recent_immunization(immunizations: list[dict[str, Any]], terms: list[str], days: int) -> bool:
    cutoff = date.today() - timedelta(days=days)
    for immunization in immunizations:
        name = immunization.get("name", "").lower()
        when = immunization.get("occurrence")
        if when and when >= cutoff and any(term in name for term in terms):
            return True
    return False


def _observation_label(resource: dict[str, Any]) -> str:
    code_text = json.dumps(resource.get("code", {})).lower()
    code_map = [
        ("a1c", ["4548-4", "17856-6", "a1c", "hemoglobin a1c"]),
        ("egfr", ["33914-3", "egfr", "glomerular filtration"]),
        ("creatinine", ["2160-0", "creatinine"]),
        ("potassium", ["2823-3", "potassium"]),
        ("hemoglobin", ["718-7", "hemoglobin"]),
        ("glucose", ["2345-7", "glucose"]),
        ("ldl", ["13457-7", "ldl"]),
        ("urine_albumin", ["14959-1", "albumin/creatinine", "urine albumin", "microalbumin"]),
        ("systolic_bp", ["8480-6", "systolic"]),
        ("diastolic_bp", ["8462-4", "diastolic"]),
    ]
    for label, terms in code_map:
        if any(term in code_text for term in terms):
            return label
    return "other"


def _high_risk_conditions(conditions: list[dict[str, Any]]) -> list[str]:
    terms = ["heart failure", "diabetes", "kidney", "ckd", "copd", "stroke", "hypertension", "depression"]
    found = []
    for condition in conditions:
        name = condition["name"]
        if _contains_any(name, terms):
            found.append(name)
    return found


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(_dedupe_findings(findings), key=lambda finding: (order.get(finding.severity, 9), finding.title))


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen = set()
    unique = []
    for finding in findings:
        key = (finding.severity, finding.title, finding.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def _code_display(concept: dict[str, Any] | None) -> str:
    if not concept:
        return ""
    if concept.get("text"):
        return concept["text"]
    coding = concept.get("coding") or []
    for item in coding:
        if item.get("display"):
            return item["display"]
    for item in coding:
        if item.get("code"):
            return item["code"]
    return ""


def _first_display(items: list[dict[str, Any]] | None) -> str:
    if not items:
        return ""
    return _code_display(items[0])


def _encounter_class(resource: dict[str, Any]) -> str:
    enc_class = resource.get("class") or {}
    return enc_class.get("display") or enc_class.get("code") or "Encounter"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _fmt_date(value: date | None) -> str:
    return value.isoformat() if value else "unknown date"


def _ref(resource: dict[str, Any]) -> str:
    return f"{resource.get('resourceType', 'Resource')}/{resource.get('id', 'unknown')}"


def _contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _meaningful_tokens(text: str) -> list[str]:
    stop = {"allergy", "allergic", "to", "and", "or", "the", "reaction"}
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) >= 4 and token not in stop]


def _obs_value(observation: dict[str, Any] | None) -> str:
    if not observation:
        return "not found"
    value = observation.get("value")
    unit = observation.get("unit") or ""
    return f"{value} {unit}".strip()


def _bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


HIGH_RISK_MED_TERMS = [
    "warfarin",
    "apixaban",
    "rivaroxaban",
    "dabigatran",
    "insulin",
    "digoxin",
    "opioid",
    "oxycodone",
    "hydrocodone",
    "morphine",
    "tramadol",
    "benzodiazepine",
    "alprazolam",
    "lorazepam",
    "diazepam",
    "clonazepam",
    "prednisone",
    "methotrexate",
    "spironolactone",
]
