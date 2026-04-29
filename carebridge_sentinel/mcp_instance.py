from mcp.server.fastmcp import FastMCP

from carebridge_sentinel.constants import FHIR_CONTEXT_EXTENSION, FHIR_SCOPES
from carebridge_sentinel.tools import (
    BuildMedicationSafetyBrief,
    CreatePostDischargeRescuePlan,
    DraftPatientOutreach,
    FindLongitudinalCareGaps,
    GenerateTransitionTaskBundle,
    GenerateTransitionOfCareBrief,
    PrioritizeTransitionPanel,
)


mcp = FastMCP("CareBridge Sentinel MCP", stateless_http=True, host="0.0.0.0")

_original_get_capabilities = mcp._mcp_server.get_capabilities


def _patched_get_capabilities(notification_options, experimental_capabilities):
    capabilities = _original_get_capabilities(notification_options, experimental_capabilities)
    capabilities.model_extra["extensions"] = {
        FHIR_CONTEXT_EXTENSION: {
            "scopes": FHIR_SCOPES,
        }
    }
    return capabilities


mcp._mcp_server.get_capabilities = _patched_get_capabilities

mcp.tool(
    name="GenerateTransitionOfCareBrief",
    description=(
        "Creates a clinician-ready, cited transition-of-care risk brief from FHIR patient context. "
        "Best for discharge follow-up, care management triage, and handoff planning."
    ),
)(GenerateTransitionOfCareBrief)

mcp.tool(
    name="FindLongitudinalCareGaps",
    description=(
        "Finds care gaps for diabetes, hypertension, CKD, and selected preventive needs using accessible FHIR data."
    ),
)(FindLongitudinalCareGaps)

mcp.tool(
    name="BuildMedicationSafetyBrief",
    description=(
        "Reviews medication, allergy, renal, and lab context to surface medication safety issues for clinician review."
    ),
)(BuildMedicationSafetyBrief)

mcp.tool(
    name="DraftPatientOutreach",
    description=(
        "Drafts a phone, portal, or SMS outreach message grounded in patient-specific transition risks and care gaps."
    ),
)(DraftPatientOutreach)

mcp.tool(
    name="CreatePostDischargeRescuePlan",
    description=(
        "Creates a 72-hour post-discharge recovery workflow with cited safety checks, medication review, "
        "follow-up closure, and longitudinal gap routing."
    ),
)(CreatePostDischargeRescuePlan)

mcp.tool(
    name="GenerateTransitionTaskBundle",
    description=(
        "Generates a draft FHIR R4 Bundle containing Task and CommunicationRequest resources "
        "for the cited post-discharge risks. Intended for clinician review before write-back."
    ),
)(GenerateTransitionTaskBundle)

mcp.tool(
    name="PrioritizeTransitionPanel",
    description=(
        "Ranks a small panel of post-acute patients by transition risk for care-manager triage. "
        "Uses synthetic demo patients by default in fixture mode, or explicit patient IDs in live mode."
    ),
)(PrioritizeTransitionPanel)
