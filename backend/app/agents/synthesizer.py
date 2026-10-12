from langfuse import observe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
import re
from app.agents.state import AgentState
from app.config import settings
from app.jobs.models import Application
from app.websocket.manager import manager


def _strip_fences(text: str) -> str:
    return re.sub(r"^```[\w]*\n?", "", re.sub(r"\n?```$", "", text.strip())).strip()


@observe(name="synthesizer", as_type="agent")
async def synthesizer_agent(state: AgentState, db: AsyncSession) -> AgentState:
    job_id = state["job_id"]

    await manager.send_progress(job_id, {
        "agent": "synthesizer",
        "status": "started",
        "message": "Saving results...",
    })

    try:
        latex = _strip_fences(state.get("tailored_resume_latex") or "")

        await db.execute(
            update(Application)
            .where(Application.id == job_id)
            .values(
                parsed_jd=state.get("parsed_jd"),
                company_research=state.get("company_research"),
                interview_questions=state.get("interview_questions"),
                tailored_resume=latex,
                tailored_resume_latex=latex,
                cover_letter=state.get("cover_letter"),
                pipeline_status="completed",
            )
        )
        await db.commit()

        await manager.send_progress(job_id, {
            "agent": "synthesizer",
            "status": "completed",
            "pipeline_status": "completed",
            "message": "Pipeline complete. All results ready.",
            "data": {
                "parsed_jd": state.get("parsed_jd"),
                "company_research_length": len(state.get("company_research") or ""),
                "cover_letter_length": len(state.get("cover_letter") or ""),
                "interview_questions_count": len(state.get("interview_questions") or []),
            },
        })

        return {
            "current_agent": "synthesizer",
            "completed_agents": ["synthesizer"],
        }

    except Exception as e:
        await db.execute(
            update(Application)
            .where(Application.id == job_id)
            .values(pipeline_status="failed")
        )
        await db.commit()
        await manager.send_progress(job_id, {
            "agent": "synthesizer",
            "status": "failed",
            "message": str(e),
        })
        return {"error": str(e)}
