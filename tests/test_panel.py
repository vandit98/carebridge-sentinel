import pytest

from carebridge_sentinel.tools import PrioritizeTransitionPanel


@pytest.mark.asyncio
async def test_transition_panel_ranks_multiple_synthetic_patients(monkeypatch):
    monkeypatch.setenv("CAREBRIDGE_SYNTHETIC_FHIR", "true")

    output = await PrioritizeTransitionPanel()

    assert "# Transition Risk Panel" in output
    assert "synthetic-patient-001" in output
    assert "synthetic-patient-002" in output
    assert "synthetic-patient-003" in output
    assert output.index("synthetic-patient-001") < output.index("synthetic-patient-003")
