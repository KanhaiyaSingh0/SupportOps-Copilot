from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AutomationKind(str, Enum):
    ASSIGNMENT = "assignment"
    MEMORY_CHECK = "memory_check"
    CPU_CHECK = "cpu_check"
    SERVICE_CHECK = "service_check"


@dataclass
class SnowIncident:
    number: str
    sys_id: str
    short_description: str
    description: str
    assignment_group: str
    server: str | None
    services: list[str]
    priority: str
    state: str


@dataclass
class ServerMetric:
    server: str
    memory_used_percent: int
    cpu_used_percent: int
    checked_at: str


@dataclass
class ServiceState:
    name: str
    status: str
    expected: str = "Running"


@dataclass
class AutomationResult:
    incident: SnowIncident
    kind: AutomationKind
    summary: str
    work_notes: str
    recommended_assignment_group: str
    metric: ServerMetric | None
    services: list[ServiceState]
    risk: str
    next_action: str


SNOW_INCIDENTS: list[SnowIncident] = [
    SnowIncident(
        "INC0010421",
        "5f9d2b8273a0230089f1d14dacf6a721",
        "Assign access request to Identity team",
        "Please assign this ticket to Identity Platform. User cannot access SSO-enabled payroll portal after role change.",
        "Service Desk",
        None,
        [],
        "P3",
        "New",
    ),
    SnowIncident(
        "INC0010422",
        "7d1b9d7e97201300f13b3b36f053af12",
        "High memory utilization on APP-SRV-014",
        "Monitoring alert says APP-SRV-014 memory usage is high. RDP details are attached in secure vault. Check memory usage and update ticket.",
        "Windows Ops",
        "APP-SRV-014",
        [],
        "P2",
        "In Progress",
    ),
    SnowIncident(
        "INC0010423",
        "8a3f0c31db1027003bfa7c53f3961901",
        "Check stopped services on DB-SRV-022",
        "Ticket requests service health check on DB-SRV-022 for MSSQLSERVER, SQLSERVERAGENT, and WinRM. Update which services are running or stopped.",
        "Database Operations",
        "DB-SRV-022",
        ["MSSQLSERVER", "SQLSERVERAGENT", "WinRM"],
        "P2",
        "New",
    ),
    SnowIncident(
        "INC0010424",
        "3c58f812c611227600f4d35c0f37ee32",
        "CPU usage alert on WEB-SRV-009",
        "CPU usage alert on WEB-SRV-009 is above 90 percent for 15 minutes. Check top utilization and update incident.",
        "Windows Ops",
        "WEB-SRV-009",
        [],
        "P2",
        "In Progress",
    ),
]


class AutomationEngine:
    def __init__(self, incidents: list[SnowIncident] | None = None) -> None:
        self.incidents = incidents or SNOW_INCIDENTS

    def list_incidents(self) -> list[SnowIncident]:
        return self.incidents

    def get_incident(self, number: str) -> SnowIncident:
        return next(incident for incident in self.incidents if incident.number == number)

    def classify(self, incident: SnowIncident) -> AutomationKind:
        text = f"{incident.short_description} {incident.description}".lower()
        if "memory" in text:
            return AutomationKind.MEMORY_CHECK
        if "cpu" in text:
            return AutomationKind.CPU_CHECK
        if "service" in text or incident.services:
            return AutomationKind.SERVICE_CHECK
        return AutomationKind.ASSIGNMENT

    def run(self, incident_number: str) -> AutomationResult:
        incident = self.get_incident(incident_number)
        kind = self.classify(incident)
        if kind == AutomationKind.MEMORY_CHECK:
            return self._memory_check(incident)
        if kind == AutomationKind.CPU_CHECK:
            return self._cpu_check(incident)
        if kind == AutomationKind.SERVICE_CHECK:
            return self._service_check(incident)
        return self._assignment(incident)

    def _assignment(self, incident: SnowIncident) -> AutomationResult:
        group = "Identity Platform" if "sso" in incident.description.lower() or "access" in incident.description.lower() else incident.assignment_group
        notes = (
            f"Automation classified {incident.number} as assignment-only. "
            f"Recommended assignment group: {group}. No server login required."
        )
        return AutomationResult(incident, AutomationKind.ASSIGNMENT, "Assignment recommendation generated.", notes, group, None, [], "Low", "Assign ticket and notify resolver group.")

    def _memory_check(self, incident: SnowIncident) -> AutomationResult:
        metric = self._metric_for(incident.server or "UNKNOWN")
        risk = "High" if metric.memory_used_percent >= 90 else "Medium"
        notes = (
            f"Checked {metric.server}. Memory utilization is {metric.memory_used_percent}%; "
            f"CPU utilization is {metric.cpu_used_percent}%. "
            "Recommended: identify top memory processes, clear approved cache if applicable, and escalate if usage remains above threshold."
        )
        return AutomationResult(incident, AutomationKind.MEMORY_CHECK, "Server memory check completed.", notes, incident.assignment_group, metric, [], risk, "Update SNOW work notes and keep ticket in progress.")

    def _cpu_check(self, incident: SnowIncident) -> AutomationResult:
        metric = self._metric_for(incident.server or "UNKNOWN")
        risk = "High" if metric.cpu_used_percent >= 90 else "Medium"
        notes = (
            f"Checked {metric.server}. CPU utilization is {metric.cpu_used_percent}%; "
            f"memory utilization is {metric.memory_used_percent}%. "
            "Recommended: capture top CPU process list, verify recent deployment/config changes, and escalate to Windows Ops if sustained."
        )
        return AutomationResult(incident, AutomationKind.CPU_CHECK, "Server CPU check completed.", notes, incident.assignment_group, metric, [], risk, "Update SNOW with metric evidence and next monitoring window.")

    def _service_check(self, incident: SnowIncident) -> AutomationResult:
        states = [ServiceState(name, self._service_status(incident.server or "", name)) for name in incident.services]
        stopped = [service.name for service in states if service.status != service.expected]
        risk = "High" if stopped else "Low"
        notes = (
            f"Checked services on {incident.server}: "
            + ", ".join(f"{service.name}={service.status}" for service in states)
            + ". "
            + ("Stopped services found: " + ", ".join(stopped) + ". Recommend restart with change policy approval." if stopped else "All requested services are running.")
        )
        return AutomationResult(incident, AutomationKind.SERVICE_CHECK, "Service status check completed.", notes, incident.assignment_group, None, states, risk, "Update ticket with service states and restart recommendation if approved.")

    def _metric_for(self, server: str) -> ServerMetric:
        metrics = {
            "APP-SRV-014": ServerMetric(server, 94, 38, "2026-06-07 18:10 IST"),
            "WEB-SRV-009": ServerMetric(server, 71, 93, "2026-06-07 18:12 IST"),
        }
        return metrics.get(server, ServerMetric(server, 64, 28, "2026-06-07 18:15 IST"))

    def _service_status(self, server: str, service: str) -> str:
        stopped = {("DB-SRV-022", "SQLSERVERAGENT")}
        return "Stopped" if (server, service) in stopped else "Running"
