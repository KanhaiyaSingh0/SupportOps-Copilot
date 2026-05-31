import asyncio

from app.config import Settings
from app.data.seed import TICKETS
from app.services import AIService, DemoStore


def test_triage_uses_ticket_severity_and_identity_route():
    store = DemoStore()
    service = AIService(Settings(app_mode="mock"), store)

    analysis = asyncio.run(service.analyze_ticket(TICKETS[0]))

    assert analysis.priority == "P1"
    assert analysis.category == "Authentication / Access"
    assert analysis.escalation_team == "Identity Platform"
    assert analysis.next_steps
    assert "Human review" in analysis.human_review_note


def test_knowledge_answer_uses_relevant_sources():
    store = DemoStore()
    service = AIService(Settings(app_mode="mock"), store)

    result = asyncio.run(service.answer_question("What should I check for 403 after deployment?"))

    assert "403" in result["sources"][0].content
    assert "Human review" in result["answer"]


def test_handover_contains_p1_and_blocked_tickets():
    store = DemoStore()
    service = AIService(Settings(app_mode="mock"), store)

    report = asyncio.run(service.generate_handover(store.list_tickets()))

    assert any("TCK-1001" in item for item in report.critical)
    assert any("TCK-1006" in item for item in report.blocked)
    assert any("P1" in action or "P2" in action for action in report.next_shift_actions)


def test_search_docs_falls_back_to_top_docs():
    store = DemoStore()

    docs = store.search_docs("nonsenseword")

    assert len(docs) == 3
