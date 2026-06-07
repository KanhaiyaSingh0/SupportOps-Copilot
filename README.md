# SupportOps Copilot

FastAPI + Azure prototype for Microsoft Build AI 2026. The app automates three common enterprise support workflows:

- Ticket triage: priority, category, SLA risk, escalation team, next steps, and customer reply draft.
- Knowledge assistant: grounded answers from support SOPs and runbooks.
- Shift handover: critical tickets, blockers, escalations, and next-shift actions.
- Version 2 automation runner: ServiceNow-style incident intake, assignment recommendation, memory checks, CPU checks, Windows service checks, and SNOW-ready work notes.

The repository uses only synthetic demo tickets and synthetic SOP documents. Do not commit real customer data or API keys.

## Version 2: SNOW And Server Automation

The v2 dashboard simulates common MNC support automations:

- Assignment-only incidents: classify and recommend the correct resolver group.
- Memory tickets: read server name from the incident, check memory/CPU metrics, and draft ServiceNow work notes.
- CPU tickets: check CPU/memory metrics and recommend escalation or monitoring.
- Service tickets: check requested Windows service names and report running/stopped state.

Current mode is safe demo mode. It does not perform real RDP login, server remediation, or ServiceNow updates.

Production connector design:

- ServiceNow: use the ServiceNow Table API to query/update `incident` records.
- Incident updates: use PUT/PATCH against the incident record and write `work_notes`, assignment group, state, and close notes as approved.
- Windows checks: use a secure remote execution path such as WinRM/PowerShell remoting, never hard-coded RDP passwords.
- Secrets: store ServiceNow credentials, Windows credentials, and vault references in Azure Key Vault or App Service settings.

Reference docs:

- ServiceNow Table API: https://www.servicenow.com/docs/r/api-reference/rest-apis/c_TableAPI.html
- ServiceNow update incident flow: https://www.servicenow.com/docs/r/api-reference/rest-api-explorer/get-started-update-incident.html
- PowerShell `Get-Counter`: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-counter

## Hackathon Fit

Theme: **AI at Work: Productivity & Teamwork Reimagined**

Microsoft stack:

- Azure OpenAI / Azure AI Foundry compatible chat-completions workflow.
- Azure App Service deployment target.
- Mock AI fallback so the demo still works while Azure access or credits are pending.

## Run Locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Azure OpenAI Configuration

Copy `.env.example` to `.env` and fill values when you have Azure OpenAI access:

```env
APP_MODE=azure
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
AZURE_OPENAI_API_KEY=YOUR_KEY
AZURE_OPENAI_DEPLOYMENT=YOUR_DEPLOYMENT
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

If these values are missing, set `APP_MODE=mock`. The app will use deterministic demo outputs.

## Deployment To Azure App Service

1. Create a resource group.
2. Create a Linux Azure App Service plan.
3. Create an Azure Web App using Python 3.11+.
4. Configure startup command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5. Add App Settings:

- `APP_MODE=azure` or `mock`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`

6. Deploy from GitHub Actions or Azure CLI.

## Demo Script

1. Open dashboard and show messy incoming support queue.
2. Select `TCK-1001`, the APAC 403 login incident.
3. Click **Analyze Ticket**.
4. Show priority, category, escalation team, next steps, missing info, and customer reply.
5. Ask Knowledge Assistant: `What should I check for 403 after deployment?`
6. Generate Shift Handover.
7. Scroll to **Version 2 / SNOW Automation**.
8. Run `INC0010422` memory automation, then `INC0010423` service automation.
9. Show SNOW-ready work notes and human approval warning.
10. End on the architecture strip: tickets + SOPs + FastAPI + Azure OpenAI + dashboard actions.

## AI Tools Disclosure

AI coding assistants and generative AI tools may be used during development. The final solution keeps human review visible in all generated operational outputs.

## Privacy And Safety

- Synthetic data only.
- No secrets in the repository.
- AI recommendations are marked for human review.
- Customer-facing messages avoid unsupported root-cause claims.
