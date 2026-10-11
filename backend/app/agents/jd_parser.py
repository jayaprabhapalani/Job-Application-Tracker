import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langfuse import observe
from tenacity import retry, stop_after_attempt, wait_exponential
from app.agents.state import AgentState
from app.config import settings
from app.websocket.manager import manager

_llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    openai_api_key=settings.OPENROUTER_API_KEY,
    openai_api_base=settings.OPENROUTER_BASE_URL,
    max_retries=0,
)

_PROMPT = """You are a job description parser. Extract structured information from the job description below.

Return ONLY a valid JSON object with exactly these keys:
{{
  "company_name": "string",
  "role_title": "string",
  "required_skills": ["string"],
  "nice_to_have_skills": ["string"],
  "experience_level": "string",
  "key_responsibilities": ["string"],
  "employment_type": "string"
}}

No markdown. No explanation. No code blocks. JSON only.

Job Description:
{jd_text}"""


def _extract_json(raw: str) -> dict:
    """Strip markdown fences and extract JSON from LLM response."""
    text = raw.strip()
    # strip ```json ... ``` or ``` ... ```
    text = re.sub(r"^```[\w]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()
    return json.loads(text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60))
async def _invoke_llm(prompt: str) -> str:
    response = await _llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()


@observe(name="jd_parser", as_type="agent")
async def jd_parser_agent(state: AgentState) -> AgentState:
    job_id = state["job_id"]

    await manager.send_progress(job_id, {
        "agent": "jd_parser",
        "status": "started",
        "message": "Parsing job description...",
    })

    try:
        prompt_text = _PROMPT.format(jd_text=state["jd_text"])
        raw = await _invoke_llm(prompt_text)
        parsed_jd = _extract_json(raw)

        await manager.send_progress(job_id, {
            "agent": "jd_parser",
            "status": "completed",
            "message": "Job description parsed.",
            "data": parsed_jd,
        })

        return {
            "parsed_jd": parsed_jd,
            "current_agent": "jd_parser",
            "completed_agents": ["jd_parser"],
        }

    except Exception as e:
        await manager.send_progress(job_id, {
            "agent": "jd_parser",
            "status": "failed",
            "message": str(e),
        })
        return {"error": str(e)}