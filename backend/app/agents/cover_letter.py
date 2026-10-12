from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langfuse import observe
from tenacity import retry, stop_after_attempt, wait_exponential
from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.config import settings
from app.websocket.manager import manager

_llm = get_llm()

_PROMPT = """You are an expert cover letter writer. Write a compelling, personalized cover letter for the job application below.

Guidelines:
- Opening: Reference something specific about the company (recent news, product, mission) from the company research.
- Body: Connect the candidate's actual experience (from the resume) to the role's key requirements. Be specific, not generic.
- Closing: Express genuine interest, mention the role title and company name explicitly.
- Tone: Professional but human. Avoid buzzwords and clichés.
- Length: 3-4 paragraphs. No more.
- Output plain text only. No markdown, no headers, no subject line.

JOB DETAILS:
Company: {company_name}
Role: {role_title}
Required Skills: {required_skills}
Key Responsibilities:
{responsibilities}

COMPANY RESEARCH:
{company_research}

CANDIDATE RESUME (tailored):
{resume_context}

Write the cover letter now."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60))
async def _invoke_llm(prompt: str) -> str:
    response = await _llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()


@observe(name="cover_letter", as_type="agent")
async def cover_letter_agent(state: AgentState) -> AgentState:
    job_id = state["job_id"]
    parsed_jd = state.get("parsed_jd", {})

    await manager.send_progress(job_id, {
        "agent": "cover_letter",
        "status": "started",
        "message": "Writing cover letter...",
    })

    try:
        prompt_text = _PROMPT.format(
            company_name=parsed_jd.get("company_name", ""),
            role_title=parsed_jd.get("role_title", ""),
            required_skills=", ".join(parsed_jd.get("required_skills", [])),
            responsibilities="\n".join(f"- {r}" for r in parsed_jd.get("key_responsibilities", [])),
            company_research=state.get("company_research") or "No company research available.",
            resume_context=state.get("tailored_resume_latex") or "No resume available.",
        )
        cover_letter = await _invoke_llm(prompt_text)

        await manager.send_progress(job_id, {
            "agent": "cover_letter",
            "status": "completed",
            "message": "Cover letter written.",
        })

        return {
            "cover_letter": cover_letter,
            "current_agent": "cover_letter",
            "completed_agents": ["cover_letter"],
        }

    except Exception as e:
        await manager.send_progress(job_id, {
            "agent": "cover_letter",
            "status": "failed",
            "message": str(e),
        })
        return {"error": str(e)}