import re
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, delete, select, text
from app.jobs.models import DocumentChunk
from app.rag.embeddings import get_embedding
from app.rag.reranker import rerank

_SECTION_PATTERNS = {
    "experience": r"(experience|work history|employment|work experience)",
    "education": r"(education|academic background|qualifications)",
    "skills": r"(skills|technologies|tech stack|tools|competencies)",
    "projects": r"(projects|portfolio|personal projects|open source)",
    "summary": r"(summary|objective|profile|about me|overview)",
}

_BULLET_SPLITTER = re.compile(r"\n(?=[-•*]|\d+\.)")


def _detect_section(line: str) -> str | None:
    line = line.lower().strip()
    for section, pattern in _SECTION_PATTERNS.items():
        if re.search(pattern, line):
            return section
    return None


def chunk_text(text: str) -> list[dict]:
    """
    Returns list of dicts with keys: id, content, chunk_level, section, parent_id, metadata.
    Parents = sections, children = bullets within each section.
    """
    lines = text.split("\n")
    sections: list[dict] = []
    current_section = "general"
    current_lines: list[str] = []

    for line in lines:
        detected = _detect_section(line)
        if detected:
            if current_lines:
                sections.append({"section": current_section, "content": "\n".join(current_lines).strip()})
            current_section = detected
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({"section": current_section, "content": "\n".join(current_lines).strip()})

    result: list[dict] = []
    for sec in sections:
        if not sec["content"]:
            continue
        parent_id = str(uuid4())
        result.append({
            "id": parent_id,
            "content": sec["content"],
            "chunk_level": "parent",
            "section": sec["section"],
            "parent_id": None,
            "metadata": {"section": sec["section"], "chunk_level": "parent"},
        })
        bullets = [b.strip() for b in _BULLET_SPLITTER.split(sec["content"]) if b.strip()]
        if len(bullets) <= 1:
            bullets = [s.strip() for s in sec["content"].split("\n") if s.strip()]
        for i, bullet in enumerate(bullets):
            result.append({
                "id": str(uuid4()),
                "content": bullet,
                "chunk_level": "child",
                "section": sec["section"],
                "parent_id": parent_id,
                "metadata": {
                    "section": sec["section"],
                    "chunk_level": "child",
                    "position": i,
                    "total_siblings": len(bullets),
                },
            })

    return result


async def store_chunks(
    db: AsyncSession,
    user_id: str,
    chunks: list[dict],
    source: str,
    extra_metadata: dict | None = None,
):
    for chunk in chunks:
        embedding = get_embedding(chunk["content"]) if chunk["chunk_level"] == "child" else None
        metadata = {**chunk["metadata"], "source": source}
        if extra_metadata:
            metadata.update(extra_metadata)
        await db.execute(
            insert(DocumentChunk).values(
                id=chunk["id"],
                user_id=user_id,
                content=chunk["content"],
                embedding=embedding,
                source=source,
                chunk_level=chunk["chunk_level"],
                parent_id=chunk["parent_id"],
                section=chunk["section"],
                metadata_=metadata,
            )
        )
    await db.commit()


async def similarity_search(
    db: AsyncSession,
    user_id: str,
    query: str,
    source: str,
    section: str | None = None,
    limit: int = 5,
) -> list[str]:
    """Hybrid search on child chunks → rerank → fetch parent chunks → return parent content."""
    embedding = get_embedding(query)
    candidate_limit = limit * 4

    # --- Vector search on child chunks ---
    filters = [
        DocumentChunk.user_id == user_id,
        DocumentChunk.source == source,
        DocumentChunk.chunk_level == "child",
    ]
    if section:
        filters.append(DocumentChunk.section == section)

    vector_rows = await db.execute(
        select(DocumentChunk.id, DocumentChunk.content, DocumentChunk.parent_id)
        .where(*filters)
        .order_by(DocumentChunk.embedding.cosine_distance(embedding))
        .limit(candidate_limit)
    )
    vector_results = {row[0]: (i + 1, row[1], row[2]) for i, row in enumerate(vector_rows.fetchall())}

    # --- Full text search on child chunks ---
    ft_query = " | ".join(re.sub(r"[^\w\s]", "", query).split())
    section_filter = "AND section = :section" if section else ""
    ft_sql = text(f"""
        SELECT id, content, parent_id
        FROM document_chunks
        WHERE user_id = :user_id
          AND source = :source
          AND chunk_level = 'child'
          {section_filter}
          AND to_tsvector('english', content) @@ to_tsquery('english', :query)
        LIMIT :limit
    """)
    params = {"user_id": user_id, "source": source, "query": ft_query, "limit": candidate_limit}
    if section:
        params["section"] = section
    ft_rows = await db.execute(ft_sql, params)
    ft_results = {row[0]: (i + 1, row[1], row[2]) for i, row in enumerate(ft_rows.fetchall())}

    # --- RRF merge ---
    all_ids = set(vector_results) | set(ft_results)
    rrf_scores: dict[str, float] = {}
    child_content: dict[str, str] = {}
    child_to_parent: dict[str, str] = {}
    k = 60
    for doc_id in all_ids:
        score = 0.0
        if doc_id in vector_results:
            rank, content, parent_id = vector_results[doc_id]
            score += 1 / (k + rank)
            child_content[doc_id] = content
            if parent_id:
                child_to_parent[doc_id] = parent_id
        if doc_id in ft_results:
            rank, content, parent_id = ft_results[doc_id]
            score += 1 / (k + rank)
            child_content[doc_id] = content
            if parent_id:
                child_to_parent[doc_id] = parent_id
        rrf_scores[doc_id] = score

    rrf_ranked = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:candidate_limit]

    # --- Rerank via Jina API ---
    if rrf_ranked:
        candidates = [child_content[doc_id] for doc_id in rrf_ranked]
        reranked_texts = await rerank(query, candidates, top_n=limit)
        text_to_id = {child_content[doc_id]: doc_id for doc_id in rrf_ranked}
        top_child_ids = [text_to_id[t] for t in reranked_texts if t in text_to_id]
    else:
        top_child_ids = rrf_ranked[:limit]

    # --- Fetch parent chunks ---
    parent_ids = list({child_to_parent[c] for c in top_child_ids if c in child_to_parent})
    if not parent_ids:
        return [child_content[c] for c in top_child_ids]

    parent_rows = await db.execute(
        select(DocumentChunk.id, DocumentChunk.content)
        .where(DocumentChunk.id.in_(parent_ids))
    )
    parent_content = {row[0]: row[1] for row in parent_rows.fetchall()}

    # Deduplicate and return parent content in ranked order
    seen: set[str] = set()
    result: list[str] = []
    for child_id in top_child_ids:
        pid = child_to_parent.get(child_id)
        if pid and pid not in seen:
            seen.add(pid)
            result.append(parent_content[pid])
        elif not pid and child_id not in seen:
            seen.add(child_id)
            result.append(child_content[child_id])

    return result


async def delete_chunks(db: AsyncSession, user_id: str, source: str):
    await db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.user_id == user_id,
            DocumentChunk.source == source,
        )
    )
    await db.commit()
