from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langfuse import observe
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.state import AgentState
from app.config import settings
from app.rag.retriever import retrieve_resume_context
from app.websocket.manager import manager

_llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    openai_api_key=settings.OPENROUTER_API_KEY,
    openai_api_base=settings.OPENROUTER_BASE_URL,
    max_retries=0,
)

_PROMPT = """You are an expert resume writer. Your task is to tailor a resume to match a specific job description.

STRICT RULES — you must follow these without exception:
1. Only use experience, skills, and achievements present in the RESUME CONTEXT below.
2. Do NOT add any skills, tools, technologies, or experience not mentioned in the resume context.
3. Do NOT fabricate metrics, dates, company names, or project names.
4. Rewrite and reorder existing bullets to emphasize relevance to the job requirements.
5. Output ONLY valid LaTeX. No explanation, no markdown, no code blocks.

JOB REQUIREMENTS:
Role: {role_title}
Required Skills: {required_skills}
Key Responsibilities: {responsibilities}
Experience Level: {experience_level}

RESUME CONTEXT (use only what is here):
{resume_context}

Output a complete, compilable LaTeX resume document tailored to this role."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60))
async def _invoke_llm(prompt: str) -> str:
    response = await _llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()


@observe(name="resume_tailor", as_type="agent")
async def resume_tailor_agent(state: AgentState, db: AsyncSession) -> AgentState:
    job_id = state["job_id"]
    user_id = state["user_id"]
    parsed_jd = state.get("parsed_jd", {})

    await manager.send_progress(job_id, {
        "agent": "resume_tailor",
        "status": "started",
        "message": "Tailoring resume...",
    })

    required_skills = parsed_jd.get("required_skills", [])
    rag_query = ", ".join(required_skills) if required_skills else state.get("jd_text", "")
    resume_context = await retrieve_resume_context(db, user_id, rag_query)

    if not resume_context:
        await manager.send_progress(job_id, {
            "agent": "resume_tailor",
            "status": "failed",
            "message": "No resume found. Please upload your resume first.",
        })
        return {"error": "No resume context found for user."}

    try:
        prompt_text = _PROMPT.format(
            role_title=parsed_jd.get("role_title", ""),
            required_skills=", ".join(required_skills),
            responsibilities="\n".join(f"- {r}" for r in parsed_jd.get("key_responsibilities", [])),
            experience_level=parsed_jd.get("experience_level", ""),
            resume_context=resume_context,
        )
        latex = await _invoke_llm(prompt_text)

        await manager.send_progress(job_id, {
            "agent": "resume_tailor",
            "status": "completed",
            "message": "Resume tailored successfully.",
        })

        return {
            "tailored_resume_latex": latex,
            "current_agent": "resume_tailor",
            "completed_agents": ["resume_tailor"],
        }

    except Exception as e:
        await manager.send_progress(job_id, {
            "agent": "resume_tailor",
            "status": "failed",
            "message": str(e),
        })
        return {"error": str(e)}