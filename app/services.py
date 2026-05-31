from __future__ import annotations

import json
from datetime import date
from typing import Any

import httpx

from app.config import Settings
from app.data.seed import KNOWLEDGE_DOCS, TICKETS
from app.models import Analysis, HandoverReport, KnowledgeDoc, Ticket


class DemoStore:
    def __init__(self) -> None:
        self.tickets = {ticket.id: ticket for ticket in TICKETS}
        self.docs = {doc.id: doc for doc in KNOWLEDGE_DOCS}
        self.analyses: dict[str, Analysis] = {}
        self.handover_reports: list[HandoverReport] = []

    def list_tickets(self) -> list[Ticket]:
        return list(self.tickets.values())

    def get_ticket(self, ticket_id: str) -> Ticket:
        return self.tickets[ticket_id]

    def search_docs(self, query: str, limit: int = 3) -> list[KnowledgeDoc]:
        terms = {term.lower().strip("?:,.") for term in query.split() if len(term) > 2}

        def score(doc: KnowledgeDoc) -> int:
            haystack = f"{doc.title} {' '.join(doc.tags)} {doc.content}".lower()
            return sum(1 for term in terms if term in haystack)

        ranked = sorted(self.docs.values(), key=score, reverse=True)
        return [doc for doc in ranked if score(doc) > 0][:limit] or ranked[:limit]


class AIService:
    def __init__(self, settings: Settings, store: DemoStore) -> None:
        self.settings = settings
        self.store = store

    async def analyze_ticket(self, ticket: Ticket) -> Analysis:
        if self.settings.use_azure:
            try:
                payload = await self._azure_json(
                    "You are a senior enterprise support triage copilot. Return strict JSON only.",
                    self._triage_prompt(ticket),
                )
                return self._analysis_from_payload(ticket.id, payload)
            except Exception:
                pass
        return self._mock_analysis(ticket)

    async def answer_question(self, question: str) -> dict[str, Any]:
        docs = self.store.search_docs(question)
        context = "\n\n".join(f"{doc.title}: {doc.content}" for doc in docs)
        if self.settings.use_azure:
            try:
                payload = await self._azure_text(
                    "Answer only from the provided support knowledge context. If missing, say what is missing.",
                    f"Question: {question}\n\nContext:\n{context}",
                )
                return {"answer": payload, "sources": docs, "mode": "Azure OpenAI"}
            except Exception:
                pass
        return {"answer": self._mock_answer(question, docs), "sources": docs, "mode": "Mock AI"}

    async def generate_handover(self, tickets: list[Ticket]) -> HandoverReport:
        if self.settings.use_azure:
            try:
                ticket_text = "\n".join(f"{t.id} | {t.severity} | {t.status} | {t.title} | {t.description}" for t in tickets)
                payload = await self._azure_json(
                    "You generate concise support shift handovers. Return strict JSON only.",
                    "Group tickets into critical, blocked, waiting_on_customer, engineering_escalated, and next_shift_actions.\n\n"
                    + ticket_text,
                )
                return HandoverReport(
                    shift_date=str(date.today()),
                    critical=payload.get("critical", []),
                    blocked=payload.get("blocked", []),
                    waiting_on_customer=payload.get("waiting_on_customer", []),
                    engineering_escalated=payload.get("engineering_escalated", []),
                    next_shift_actions=payload.get("next_shift_actions", []),
                )
            except Exception:
                pass
        return self._mock_handover(tickets)

    async def _azure_json(self, system: str, user: str) -> dict[str, Any]:
        text = await self._azure_text(system, user)
        return json.loads(text)

    async def _azure_text(self, system: str, user: str) -> str:
        endpoint = self.settings.azure_openai_endpoint.rstrip("/")
        deployment = self.settings.azure_openai_deployment
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"
        params = {"api-version": self.settings.azure_openai_api_version}
        headers = {"api-key": self.settings.azure_openai_api_key, "Content-Type": "application/json"}
        body = {
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,
            "max_tokens": 900,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params, headers=headers, json=body)
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _triage_prompt(self, ticket: Ticket) -> str:
        return (
            "Analyze this support ticket and return JSON with priority, category, confidence, "
            "business_impact, affected_users, urgency_reason, missing_info, next_steps, escalation_team, customer_reply.\n\n"
            f"{ticket}"
        )

    def _analysis_from_payload(self, ticket_id: str, payload: dict[str, Any]) -> Analysis:
        return Analysis(
            ticket_id=ticket_id,
            priority=payload.get("priority", "P3"),
            category=payload.get("category", "General Support"),
            confidence=payload.get("confidence", "Medium"),
            business_impact=payload.get("business_impact", "Impact needs confirmation."),
            affected_users=str(payload.get("affected_users", "Unknown")),
            urgency_reason=payload.get("urgency_reason", "SLA risk should be reviewed."),
            missing_info=list(payload.get("missing_info", [])),
            next_steps=list(payload.get("next_steps", [])),
            escalation_team=payload.get("escalation_team", "Support Operations"),
            customer_reply=payload.get("customer_reply", "We are investigating and will share the next update soon."),
        )

    def _mock_analysis(self, ticket: Ticket) -> Analysis:
        lower = f"{ticket.title} {ticket.description}".lower()
        if "403" in lower or "sso" in lower or "login" in lower:
            category = "Authentication / Access"
            team = "Identity Platform"
            steps = ["Check auth deployment id and changed policies.", "Compare SSO claims for affected APAC tenant.", "Validate role mapping and rollback risky policy changes.", "Post next customer update within 30 minutes."]
        elif "azure" in lower or "aks" in lower or "redis" in lower or "cpu" in lower:
            category = "Cloud Operations"
            team = "Cloud Operations"
            steps = ["Check correlated deployments and Azure metrics.", "Assign incident commander if P1.", "Capture resource, region, subscription, and metric values.", "Mitigate capacity or rollback recent config change."]
        elif "billing" in lower or "invoice" in lower or "charge" in lower:
            category = "Billing / Account"
            team = "Finance Ops"
            steps = ["Verify invoice id and processor event id.", "Check renewal date and plan history.", "Avoid refund commitment until finance confirms.", "Send acknowledgement with review timeline."]
        else:
            category = "Application Support"
            team = "Application Engineering"
            steps = ["Collect logs, timestamps, tenant id, and recent changes.", "Confirm business impact and workaround.", "Search known incidents and related tickets.", "Escalate with concise reproduction details."]

        confidence = "High" if ticket.severity in {"P1", "P2"} else "Medium"
        return Analysis(
            ticket_id=ticket.id,
            priority=ticket.severity,
            category=category,
            confidence=confidence,
            business_impact=self._impact(ticket),
            affected_users=self._affected_users(ticket.description),
            urgency_reason=f"{ticket.severity} ticket with SLA due {ticket.sla_due_at}.",
            missing_info=["Tenant id", "Recent deployment id", "Exact error screenshot"] if "tenant" not in lower else ["Deployment id", "Full log correlation id"],
            next_steps=steps,
            escalation_team=team,
            customer_reply=(
                f"Hi {ticket.customer}, we acknowledge the reported issue and have classified it as {ticket.severity}. "
                f"Our {team} team is investigating the likely {category.lower()} path. "
                "We will share the next update after validating impact and mitigation options."
            ),
        )

    def _mock_answer(self, question: str, docs: list[KnowledgeDoc]) -> str:
        if not docs:
            return "I do not have enough SOP context to answer this safely. Add the relevant runbook and retry."
        top = docs[0]
        answer = top.content.split(". ")[:3]
        return " ".join(answer) + ". Human review required before acting on this recommendation."

    def _mock_handover(self, tickets: list[Ticket]) -> HandoverReport:
        critical = [f"{t.id}: {t.title} ({t.sla_due_at})" for t in tickets if t.severity == "P1"]
        blocked = [f"{t.id}: {t.title}" for t in tickets if t.status == "Blocked"]
        waiting = [f"{t.id}: {t.title}" for t in tickets if t.status == "Waiting on Customer"]
        escalated = [f"{t.id}: {t.title}" for t in tickets if t.status == "Engineering Escalated"]
        next_actions = [
            "Send 30-minute updates for all P1 tickets until mitigation.",
            "Confirm SLA risk for open P2 tickets due in the next two hours.",
            "Attach deployment ids, tenant ids, and metric screenshots before escalation.",
            "Prepare customer-safe RCA summaries only after engineering validates root cause.",
        ]
        return HandoverReport(str(date.today()), critical, blocked, waiting, escalated, next_actions)

    def _impact(self, ticket: Ticket) -> str:
        if ticket.severity == "P1":
            return "High production impact; immediate incident workflow recommended."
        if ticket.severity == "P2":
            return "Meaningful business impact or near-term SLA risk."
        return "Limited impact or workaround likely available."

    def _affected_users(self, description: str) -> str:
        words = description.replace(".", " ").split()
        for index, word in enumerate(words):
            if word.isdigit():
                suffix = " ".join(words[index : index + 3])
                return suffix
        return "Unknown; ask customer to confirm affected users."
