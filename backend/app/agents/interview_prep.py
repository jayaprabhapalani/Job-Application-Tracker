import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langfuse import observe
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.config import settings
from app.rag.retriever import retrieve_interview_context
from app.websocket.manager import manager

_llm = get_llm()

_PROMPT = """You are an expert interview coach. Generate exactly 10 interview questions for the role below.

STRICT CATEGORY BREAKDOWN:
- 5 technical questions (based on required skills and responsibilities)
- 3 behavioral questions (STAR format, relevant to the role)
- 2 company-specific questions (based on company name and research)

Return ONLY a valid JSON array of exactly 10 objects. No markdown. No explanation. JSON only.
Each object must have exactly these keys:
  "question": the interview question (string)
  "category": one of "technical", "behavioral", "company_specific" (string)
  "hint": a brief answer hint or what the interviewer is looking for (string)

Role: {role_title}
Company: {company_name}
Required Skills: {required_skills}
Key Responsibilities:
{key_responsibilities}

PAST INTERVIEW CONTEXT (use if relevant, do not fabricate):
{interview_context}"""


def _extract_json(raw: str) -> list:
    text = raw.strip()
    text = re.sub(r"^```[\w]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()
    return json.loads(text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60))
async def _invoke_llm(prompt: str) -> str:
    response = await _llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()


@observe(name="interview_prep", as_type="agent")
async def interview_prep_agent(state: AgentState, db: AsyncSession) -> AgentState:
    job_id = state["job_id"]
    user_id = state["user_id"]
    parsed_jd = state.get("parsed_jd", {})

    await manager.send_progress(job_id, {
        "agent": "interview_prep",
        "status": "started",
        "message": "Generating interview questions...",
    })

    role_title = parsed_jd.get("role_title", "")
    required_skills = parsed_jd.get("required_skills", [])
    rag_query = f"{role_title} {', '.join(required_skills)}".strip()
    company_name = parsed_jd.get("company_name", "")

    interview_context = await retrieve_interview_context(db, user_id, rag_query, company=company_name)

    try:
        prompt_text = _PROMPT.format(
            role_title=role_title,
            company_name=company_name,
            required_skills=", ".join(required_skills),
            key_responsibilities="\n".join(f"- {r}" for r in parsed_jd.get("key_responsibilities", [])),
            interview_context=interview_context or "No prior interview context available.",
        )
        raw = await _invoke_llm(prompt_text)
        questions = _extract_json(raw)

        await manager.send_progress(job_id, {
            "agent": "interview_prep",
            "status": "completed",
            "message": f"Generated {len(questions)} interview questions.",
        })

        return {
            "interview_questions": questions,
            "current_agent": "interview_prep",
            "completed_agents": ["interview_prep"],
        }

    except Exception as e:
        await manager.send_progress(job_id, {
            "agent": "interview_prep",
            "status": "failed",
            "message": str(e),
        })
        return {"error": str(e)}