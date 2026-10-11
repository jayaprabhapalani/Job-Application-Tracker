import httpx
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

_JINA_HEADERS = {
    "Authorization": f"Bearer {settings.JINA_API_KEY}",
    "Accept": "text/plain",
}

_PROMPT = """You are a company research analyst. Based on the raw content below, write a concise research summary.

Cover these sections:
1. What the company does (product/service, market, customers)
2. Tech stack they use (from job postings, engineering blog, etc.)
3. Recent news (funding, launches, acquisitions, layoffs)
4. Culture and values
5. Funding status / company stage (if available)

Be factual. Use only information present in the content. If a section has no data, write "Not found."

Company: {company_name}

--- WEBSITE CONTENT ---
{website_content}

--- NEWS CONTENT ---
{news_content}"""


async def _fetch_jina(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=_JINA_HEADERS)
            response.raise_for_status()
            return response.text[:8000]
    except Exception:
        return ""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60))
async def _invoke_llm(prompt: str) -> str:
    response = await _llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()


@observe(name="company_research", as_type="agent")
async def company_research_agent(state: AgentState) -> AgentState:
    job_id = state["job_id"]
    company_name = state.get("parsed_jd", {}).get("company_name", "")
    company_slug = company_name.lower().replace(" ", "")
    company_website = f"https://www.{company_slug}.com"

    await manager.send_progress(job_id, {
        "agent": "company_research",
        "status": "started",
        "message": f"Researching {company_name}...",
    })

    website_content = await _fetch_jina(f"https://r.jina.ai/{company_website}")
    news_url = f"https://s.jina.ai/{company_name.replace(' ', '%20')}%20latest%20news"
    news_content = await _fetch_jina(news_url)

    try:
        prompt_text = _PROMPT.format(
            company_name=company_name,
            website_content=website_content or "No website content retrieved.",
            news_content=news_content or "No news content retrieved.",
        )
        research = await _invoke_llm(prompt_text)

        await manager.send_progress(job_id, {
            "agent": "company_research",
            "status": "completed",
            "message": "Company research complete.",
        })

        return {
            "company_research": research,
            "current_agent": "company_research",
            "completed_agents": ["company_research"],
        }

    except Exception as e:
        await manager.send_progress(job_id, {
            "agent": "company_research",
            "status": "failed",
            "message": str(e),
        })
        return {"error": str(e)}