import asyncio
from functools import partial
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from app.agents.state import AgentState
from app.agents.jd_parser import jd_parser_agent
from app.agents.company_research import company_research_agent
from app.agents.interview_prep import interview_prep_agent
from app.agents.resume_tailor import resume_tailor_agent
from app.agents.cover_letter import cover_letter_agent
from app.agents.synthesizer import synthesizer_agent
from app.guardrails.output_validator import guardrails_agent
from app.database import AsyncSessionLocal
from app.websocket.manager import manager
from langfuse import observe


def _route_after_jd_parser(state: AgentState):
    return [
        Send("company_research", state),
        Send("interview_prep", state),
    ]


def _route_after_guardrails(state: AgentState):
    if state.get("validation_passed"):
        return "synthesizer"
    return "fail_pipeline"


async def _fail_pipeline_node(state: AgentState) -> AgentState:
    from sqlalchemy import update
    from app.jobs.models import Application
    job_id = state["job_id"]
    errors = state.get("validation_errors", [])
    async with AsyncSessionLocal() as db:
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


def _build_graph(db) -> StateGraph:
    graph = StateGraph(AgentState)

    # Wrap db-dependent agents
    interview_prep_node = partial(interview_prep_agent, db=db)
    resume_tailor_node = partial(resume_tailor_agent, db=db)
    synthesizer_node = partial(synthesizer_agent, db=db)

    graph.add_node("jd_parser", jd_parser_agent)
    graph.add_node("company_research", company_research_agent)
    graph.add_node("interview_prep", interview_prep_node)
    graph.add_node("resume_tailor", resume_tailor_node)
    graph.add_node("cover_letter", cover_letter_agent)
    graph.add_node("guardrails", guardrails_agent)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("fail_pipeline", _fail_pipeline_node)

    graph.add_edge(START, "jd_parser")
    graph.add_conditional_edges("jd_parser", _route_after_jd_parser)
    graph.add_edge("company_research", "resume_tailor")
    graph.add_edge("interview_prep", "resume_tailor")
    graph.add_edge("resume_tailor", "cover_letter")
    graph.add_edge("cover_letter", "guardrails")
    graph.add_conditional_edges("guardrails", _route_after_guardrails)
    graph.add_edge("fail_pipeline", END)
    graph.add_edge("synthesizer", END)

    return graph.compile()


@observe(name="pipeline", as_type="agent")
async def run_pipeline(job_id: str, user_id: str, jd_text: str, db) -> AgentState:
    pipeline = _build_graph(db)
    initial_state: AgentState = {
        "job_id": job_id,
        "user_id": user_id,
        "jd_text": jd_text,
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
    }
    return await pipeline.ainvoke(initial_state)
