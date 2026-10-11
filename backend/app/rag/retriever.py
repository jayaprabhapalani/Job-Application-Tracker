from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.vector_store import similarity_search


async def retrieve_resume_context(
    db: AsyncSession,
    user_id: str,
    query: str,
    section: str | None = None,
) -> str:
    chunks = await similarity_search(db, user_id, query, source="resume", section=section)
    return "\n\n".join(chunks)


async def retrieve_interview_context(
    db: AsyncSession,
    user_id: str,
    query: str,
    company: str | None = None,
) -> str:
    chunks = await similarity_search(db, user_id, query, source="interview_notes")
    return "\n\n".join(chunks)
