from langchain_openai import ChatOpenAI
from app.config import settings


def get_llm():
    """
    Returns primary LLM (Groq) with fallback (OpenRouter/Gemini).
    Groq is used as primary for fast inference and to avoid Gemini rate limits.
    If Groq fails or rate limits, it automatically falls back to OpenRouter.
    """
    if settings.GROQ_API_KEY:
        primary = ChatOpenAI(
            model=settings.GROQ_MODEL,
            openai_api_key=settings.GROQ_API_KEY,
            openai_api_base=settings.GROQ_BASE_URL,
            max_retries=1,
        )
        fallback = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            max_retries=1,
        )
        return primary.with_fallbacks([fallback])

    return ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.OPENROUTER_BASE_URL,
        max_retries=2,
    )
