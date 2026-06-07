from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_loads():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "SupportOps Copilot" in response.text
    assert "Incoming Queue" in response.text


def test_analyze_ticket_partial():
    client = TestClient(app)

    response = client.post("/tickets/TCK-1001/analyze")

    assert response.status_code == 200
    assert "Identity Platform" in response.text
    assert "Draft Customer Reply" in response.text


def test_v2_automation_route_generates_work_notes():
    client = TestClient(app)

    response = client.post("/automation/INC0010422/run")

    assert response.status_code == 200
    assert "SNOW Work Notes Draft" in response.text
    assert "Memory utilization" in response.text
