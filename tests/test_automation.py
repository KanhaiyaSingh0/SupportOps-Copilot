from app.automation import AutomationEngine, AutomationKind


def test_classifies_memory_incident():
    engine = AutomationEngine()

    incident = engine.get_incident("INC0010422")

    assert engine.classify(incident) == AutomationKind.MEMORY_CHECK


def test_memory_automation_generates_metric_work_notes():
    engine = AutomationEngine()

    result = engine.run("INC0010422")

    assert result.metric is not None
    assert result.metric.memory_used_percent == 94
    assert "Memory utilization" in result.work_notes
    assert result.risk == "High"


def test_service_automation_finds_stopped_service():
    engine = AutomationEngine()

    result = engine.run("INC0010423")

    assert result.kind == AutomationKind.SERVICE_CHECK
    assert any(service.name == "SQLSERVERAGENT" and service.status == "Stopped" for service in result.services)
    assert "Stopped services found" in result.work_notes


def test_assignment_automation_routes_identity_ticket():
    engine = AutomationEngine()

    result = engine.run("INC0010421")

    assert result.kind == AutomationKind.ASSIGNMENT
    assert result.recommended_assignment_group == "Identity Platform"
