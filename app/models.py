from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    customer: str
    domain: str
    product: str
    severity: str
    status: str
    created_at: str
    sla_due_at: str


@dataclass
class Analysis:
    ticket_id: str
    priority: str
    category: str
    confidence: str
    business_impact: str
    affected_users: str
    urgency_reason: str
    missing_info: list[str]
    next_steps: list[str]
    escalation_team: str
    customer_reply: str
    human_review_note: str = "Human review required before customer-facing or operational action."


@dataclass
class KnowledgeDoc:
    id: str
    title: str
    source: str
    content: str
    tags: list[str] = field(default_factory=list)


@dataclass
class HandoverReport:
    shift_date: str
    critical: list[str]
    blocked: list[str]
    waiting_on_customer: list[str]
    engineering_escalated: list[str]
    next_shift_actions: list[str]
    human_review_note: str = "Human review required before publishing the handover."
