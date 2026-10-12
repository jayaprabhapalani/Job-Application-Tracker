import asyncio
from functools import partial
from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.jd_parser import jd_parser_agent
from app.agents.company_research import company_research_agent
from app.agents.interview_prep import interview_prep_agent
from app.agents.resume_tailor import resume_tailor_agent
from app.agents.cover_letter import cover_letter_agent
from app.agents.synthesizer import synthesizer_agent
from app.guardrails.output_validator import guardrails_agent
from app.websocket.manager import manager
from langfuse import observe

import time
from app.monitoring.metrics import agent_duration_seconds


def _timed(name, fn):
    async def _wrapped(*args, **kwargs):
        start_time = time.monotonic()
        try:
            return await fn(*args, **kwargs)
        finally:
            agent_duration_seconds.labels(agent_name=name).observe(time.monotonic() - start_time)
    return _wrapped


def _with_session(fn, session_factory):
    """Wrap a db-dependent agent so it opens its own session per call."""
    async def _wrapped(state: AgentState):
        async with session_factory() as db:
            return await fn(state, db=db)
    return _wrapped


def _route_after_guardrails(state: AgentState):
    if state.get("validation_passed"):
        return "synthesizer"
    return "fail_pipeline"


async def _fail_pipeline_node(state: AgentState) -> AgentState:
    from sqlalchemy import update
    from app.jobs.models import Application
    job_id = state["job_id"]
    errors = state.get("validation_errors", [])
    async with state["_session_factory"]() as db:
        await db.execute(
            update(Application)
            .where(Application.id == job_id)
            .values(pipeline_status="failed")
        )
        await db.commit()
    await manager.send_progress(job_id, {
        "agent": "guardrails",
        "status": "failed",
        "message": f"Pipeline failed validation: {'; '.join(errors)}",
    })
    return state


def _build_graph(session_factory) -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("jd_parser", _timed("jd_parser", jd_parser_agent))
    graph.add_node("company_research", _timed("company_research", company_research_agent))
    graph.add_node("interview_prep", _timed("interview_prep", _with_session(interview_prep_agent, session_factory)))
    graph.add_node("resume_tailor", _timed("resume_tailor", _with_session(resume_tailor_agent, session_factory)))
    graph.add_node("cover_letter", _timed("cover_letter", cover_letter_agent))
    graph.add_node("guardrails", _timed("guardrails", guardrails_agent))
    graph.add_node("synthesizer", _timed("synthesizer", _with_session(synthesizer_agent, session_factory)))
    graph.add_node("fail_pipeline", _fail_pipeline_node)

    graph.add_edge(START, "jd_parser")
    graph.add_edge("jd_parser", "company_research")
    graph.add_edge("company_research", "interview_prep")
    graph.add_edge("interview_prep", "resume_tailor")
    graph.add_edge("resume_tailor", "cover_letter")
    graph.add_edge("cover_letter", "guardrails")
    graph.add_conditional_edges("guardrails", _route_after_guardrails)
    graph.add_edge("fail_pipeline", END)
    graph.add_edge("synthesizer", END)

    return graph.compile()


@observe(name="pipeline", as_type="agent")
async def run_pipeline(job_id: str, user_id: str, jd_text: str, session_factory, company: str = "", role: str = "") -> AgentState:
    pipeline = _build_graph(session_factory)
    initial_state: AgentState = {
        "job_id": job_id,
        "user_id": user_id,
        "jd_text": jd_text,
        "company": company,
        "role": role,
        "parsed_jd": {},
        "company_research": "",
        "interview_questions": [],
        "tailored_resume_latex": "",
        "cover_letter": "",
        "validation_passed": False,
        "validation_errors": [],
        "completed_agents": [],
        "current_agent": "",
        "error": "",
        "_session_factory": session_factory,
    }
    return await pipeline.ainvoke(initial_state)
