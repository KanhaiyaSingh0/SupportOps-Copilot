from __future__ import annotations

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.automation import AutomationEngine
from app.config import get_settings
from app.services import AIService, DemoStore

settings = get_settings()
store = DemoStore()
ai = AIService(settings, store)
automation = AutomationEngine()

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    tickets = store.list_tickets()
    selected = tickets[0]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "tickets": tickets,
            "selected": selected,
            "ticket": selected,
            "analysis": store.analyses.get(selected.id),
            "answer": None,
            "sources": [],
            "handover": None,
            "snow_incidents": automation.list_incidents(),
            "settings": settings,
        },
    )


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_id: str) -> HTMLResponse:
    if ticket_id not in store.tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return templates.TemplateResponse(
        request,
        "partials/ticket_detail.html",
        {"request": request, "ticket": store.get_ticket(ticket_id), "analysis": store.analyses.get(ticket_id)},
    )


@app.post("/tickets/{ticket_id}/analyze", response_class=HTMLResponse)
async def analyze_ticket(request: Request, ticket_id: str) -> HTMLResponse:
    if ticket_id not in store.tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket = store.get_ticket(ticket_id)
    analysis = await ai.analyze_ticket(ticket)
    store.analyses[ticket_id] = analysis
    return templates.TemplateResponse(request, "partials/analysis.html", {"request": request, "ticket": ticket, "analysis": analysis})


@app.post("/knowledge", response_class=HTMLResponse)
async def ask_knowledge(request: Request, question: str = Form(...)) -> HTMLResponse:
    result = await ai.answer_question(question)
    return templates.TemplateResponse(
        request,
        "partials/knowledge_answer.html",
        {"request": request, "question": question, "answer": result["answer"], "sources": result["sources"], "mode": result["mode"]},
    )


@app.post("/handover", response_class=HTMLResponse)
async def handover(request: Request) -> HTMLResponse:
    report = await ai.generate_handover(store.list_tickets())
    store.handover_reports.append(report)
    return templates.TemplateResponse(request, "partials/handover.html", {"request": request, "handover": report})


@app.post("/automation/{incident_number}/run", response_class=HTMLResponse)
async def run_automation(request: Request, incident_number: str) -> HTMLResponse:
    try:
        result = automation.run(incident_number)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Incident not found") from None
    return templates.TemplateResponse(request, "partials/automation_result.html", {"request": request, "result": result})


@app.post("/seed")
async def seed_demo() -> RedirectResponse:
    store.analyses.clear()
    store.handover_reports.clear()
    return RedirectResponse("/", status_code=303)
