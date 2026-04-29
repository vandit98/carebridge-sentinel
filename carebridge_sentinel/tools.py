from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from carebridge_sentinel.clinical import (
    build_snapshot,
    care_gap_brief,
    medication_safety_brief,
    outreach_draft,
    panel_transition_summary,
    post_discharge_rescue_plan,
    risk_tier,
    transition_task_bundle,
    transition_brief,
    transition_findings,
)
from carebridge_sentinel.fhir import SyntheticFhirClient, fetch_patient_record, get_client, get_fhir_context, resolve_patient_id


async def GenerateTransitionOfCareBrief(
    patientId: Annotated[
        str | None,
        Field(description="FHIR Patient.id. Optional when Prompt Opinion passes patient context."),
    ] = None,
    lookbackDays: Annotated[
        int,
        Field(description="Number of days to emphasize for recent transition risk.", ge=7, le=180),
    ] = 45,
    ctx: Context | None = None,
) -> str:
    """Build a cited transition-of-care risk brief from FHIR context."""

    record = await _record(patientId, lookbackDays, ctx)
    return transition_brief(record)


async def FindLongitudinalCareGaps(
    patientId: Annotated[
        str | None,
        Field(description="FHIR Patient.id. Optional when Prompt Opinion passes patient context."),
    ] = None,
    lookbackDays: Annotated[
        int,
        Field(description="Lookback window used for fetching patient context.", ge=30, le=730),
    ] = 365,
    ctx: Context | None = None,
) -> str:
    """Find diabetes, hypertension, kidney, and preventive care gaps."""

    record = await _record(patientId, lookbackDays, ctx)
    return care_gap_brief(record)


async def BuildMedicationSafetyBrief(
    patientId: Annotated[
        str | None,
        Field(description="FHIR Patient.id. Optional when Prompt Opinion passes patient context."),
    ] = None,
    lookbackDays: Annotated[
        int,
        Field(description="Lookback window used for fetching patient context.", ge=30, le=730),
    ] = 365,
    ctx: Context | None = None,
) -> str:
    """Review medication safety signals using meds, allergies, and recent labs."""

    record = await _record(patientId, lookbackDays, ctx)
    return medication_safety_brief(record)


async def DraftPatientOutreach(
    patientId: Annotated[
        str | None,
        Field(description="FHIR Patient.id. Optional when Prompt Opinion passes patient context."),
    ] = None,
    channel: Annotated[
        str,
        Field(description="Desired draft channel: phone, portal, or sms."),
    ] = "phone",
    lookbackDays: Annotated[
        int,
        Field(description="Lookback window used for fetching patient context.", ge=7, le=180),
    ] = 45,
    ctx: Context | None = None,
) -> str:
    """Draft patient outreach for clinician review, grounded in FHIR-derived risks."""

    record = await _record(patientId, lookbackDays, ctx)
    return outreach_draft(record, channel)


async def CreatePostDischargeRescuePlan(
    patientId: Annotated[
        str | None,
        Field(description="FHIR Patient.id. Optional when Prompt Opinion passes patient context."),
    ] = None,
    lookbackDays: Annotated[
        int,
        Field(description="Lookback window used for recent transition risk.", ge=7, le=180),
    ] = 45,
    ctx: Context | None = None,
) -> str:
    """Create a 72-hour recovery workflow after discharge or acute care."""

    record = await _record(patientId, lookbackDays, ctx)
    return post_discharge_rescue_plan(record)


async def GenerateTransitionTaskBundle(
    patientId: Annotated[
        str | None,
        Field(description="FHIR Patient.id. Optional when Prompt Opinion passes patient context."),
    ] = None,
    lookbackDays: Annotated[
        int,
        Field(description="Lookback window used for recent transition risk.", ge=7, le=180),
    ] = 45,
    ctx: Context | None = None,
) -> str:
    """Generate draft FHIR Task and CommunicationRequest resources for clinician review."""

    record = await _record(patientId, lookbackDays, ctx)
    return transition_task_bundle(record)


async def PrioritizeTransitionPanel(
    patientIds: Annotated[
        str | None,
        Field(description="Comma-separated FHIR Patient.id values. Optional in synthetic demo mode."),
    ] = None,
    lookbackDays: Annotated[
        int,
        Field(description="Lookback window used for recent transition risk.", ge=7, le=180),
    ] = 45,
    maxPatients: Annotated[
        int,
        Field(description="Maximum number of patients to evaluate.", ge=1, le=25),
    ] = 10,
    ctx: Context | None = None,
) -> str:
    """Rank a small transition panel for care-manager triage."""

    context = get_fhir_context(ctx)
    client = get_client(context)
    ids = _parse_patient_ids(patientIds)
    if not ids:
        if isinstance(client, SyntheticFhirClient):
            ids = client.patient_ids()
        elif context.patient_id:
            ids = [context.patient_id]
        else:
            raise ValueError("Provide patientIds, or use synthetic demo mode with CAREBRIDGE_SYNTHETIC_FHIR=true.")

    rows = []
    for patient_id in ids[:maxPatients]:
        record = await fetch_patient_record(client, patient_id, lookbackDays)
        snapshot = build_snapshot(record)
        findings = transition_findings(snapshot)
        tier, score = risk_tier(findings)
        rows.append(
            {
                "patientId": patient_id,
                "patientLabel": snapshot["patientLabel"],
                "riskTier": tier,
                "riskScore": score,
                "topDrivers": [finding.title for finding in findings[:4]],
                "evidence": [ref for finding in findings[:4] for ref in finding.evidence],
            }
        )

    return panel_transition_summary(rows)


async def _record(patient_id: str | None, lookback_days: int, ctx: Context | None) -> dict:
    context = get_fhir_context(ctx)
    resolved_patient_id = resolve_patient_id(patient_id, context)
    client = get_client(context)
    return await fetch_patient_record(client, resolved_patient_id, lookback_days)


def _parse_patient_ids(patient_ids: str | None) -> list[str]:
    if not patient_ids:
        return []
    return [item.strip() for item in patient_ids.split(",") if item.strip()]
