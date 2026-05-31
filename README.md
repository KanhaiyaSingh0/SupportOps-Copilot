# SupportOps Copilot

FastAPI + Azure prototype for Microsoft Build AI 2026. The app automates three common enterprise support workflows:

- Ticket triage: priority, category, SLA risk, escalation team, next steps, and customer reply draft.
- Knowledge assistant: grounded answers from support SOPs and runbooks.
- Shift handover: critical tickets, blockers, escalations, and next-shift actions.

The repository uses only synthetic demo tickets and synthetic SOP documents. Do not commit real customer data or API keys.

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
7. End on the architecture strip: tickets + SOPs + FastAPI + Azure OpenAI + dashboard actions.

## AI Tools Disclosure

AI coding assistants and generative AI tools may be used during development. The final solution keeps human review visible in all generated operational outputs.

## Privacy And Safety

- Synthetic data only.
- No secrets in the repository.
- AI recommendations are marked for human review.
- Customer-facing messages avoid unsupported root-cause claims.
