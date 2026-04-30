from fastapi.testclient import TestClient

from carebridge_sentinel.main import app


def test_plugin_health_endpoint():
    client = TestClient(app)

    response = client.get("/api/plugin/health")

    assert response.status_code == 200
    assert response.json()["service"] == "carebridge-sentinel-plugin-api"


def test_plugin_transition_panel_uses_synthetic_fixture(monkeypatch):
    monkeypatch.setenv("CAREBRIDGE_SYNTHETIC_FHIR", "true")
    client = TestClient(app)

    response = client.post("/api/plugin/prioritize-transition-panel", json={"maxPatients": 3})

    assert response.status_code == 200
    payload = response.json()
    assert "synthetic-patient-001" in payload["result"]
    assert "Clinician-review decision support" in payload["safetyNote"]


def test_plugin_transition_brief_accepts_patient_id(monkeypatch):
    monkeypatch.setenv("CAREBRIDGE_SYNTHETIC_FHIR", "true")
    client = TestClient(app)

    response = client.post(
        "/api/plugin/transition-brief",
        json={"patientId": "synthetic-patient-001", "lookbackDays": 45},
    )

    assert response.status_code == 200
    assert "synthetic-patient-001" in response.json()["result"]
