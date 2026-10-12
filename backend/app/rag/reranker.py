import httpx
from app.config import settings

_JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"
_MODEL = "jina-reranker-v2-base-multilingual"


async def rerank(query: str, chunks: list[str], top_n: int = 5) -> list[str]:
    if not chunks:
        return []
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _JINA_RERANK_URL,
            headers={"Authorization": f"Bearer {settings.JINA_API_KEY}"},
            json={
                "model": _MODEL,
                "query": query,
                "documents": chunks,
                "top_n": top_n,
            },
            timeout=30.0,
        )
        response.raise_for_status()
    results = response.json()["results"]
    return [r["document"] if isinstance(r, dict) else r for r in results]
