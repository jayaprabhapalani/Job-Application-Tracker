"""
Offline RAG evaluation using RAGAS.
Run manually against a sample of retrievals/generations — not part of the live pipeline.

Usage:
    python -m app.evaluation.rag_eval
"""
import uuid
from langfuse import Langfuse
from ragas import evaluate, EvaluationDataset
from ragas.metrics import ContextPrecision, ContextRecall, Faithfulness, AnswerRelevancy
from ragas.llms import LangchainLLMWrapper
from langchain_anthropic import ChatAnthropic
from app.config import settings

_lf = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
)

_llm = LangchainLLMWrapper(ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    api_key=settings.ANTHROPIC_API_KEY,
))


def _log_scores(trace_id: str, scores: dict[str, float], eval_type: str) -> None:
    for metric_name, value in scores.items():
        _lf.score(
            trace_id=trace_id,
            name=f"{eval_type}/{metric_name}",
            value=value,
            comment=f"RAGAS {eval_type} evaluation",
        )
    _lf.flush()


def evaluate_retrieval(
    question: str,
    retrieved_chunks: list[str],
    ground_truth: str,
) -> dict[str, float]:
    """
    Evaluate retrieval quality for a single sample.

    Args:
        question:         The query sent to the retriever (e.g. job skills string).
        retrieved_chunks: List of chunk strings returned by similarity_search.
        ground_truth:     The ideal answer / reference text for this query.

    Returns:
        Dict with context_precision and context_recall scores (0-1).
    """
    dataset = EvaluationDataset.from_list([{
        "user_input": question,
        "retrieved_contexts": retrieved_chunks,
        "reference": ground_truth,
    }])

    result = evaluate(
        dataset=dataset,
        metrics=[ContextPrecision(), ContextRecall()],
        llm=_llm,
    )

    scores = {
        "context_precision": float(result["context_precision"]),
        "context_recall": float(result["context_recall"]),
    }

    trace_id = str(uuid.uuid4())
    trace = _lf.trace(
        id=trace_id,
        name="ragas_retrieval_eval",
        input={"question": question, "retrieved_chunks": retrieved_chunks},
        output=scores,
        tags=["ragas", "retrieval"],
    )
    _log_scores(trace_id, scores, "retrieval")

    return scores


def evaluate_generation(
    question: str,
    answer: str,
    retrieved_chunks: list[str],
) -> dict[str, float]:
    """
    Evaluate generation quality for a single sample.

    Args:
        question:         The original question / job requirement prompt.
        answer:           The LLM-generated output (e.g. tailored resume section).
        retrieved_chunks: The context chunks that were fed to the LLM.

    Returns:
        Dict with faithfulness and answer_relevancy scores (0-1).
        faithfulness < 0.8 indicates likely hallucination.
    """
    dataset = EvaluationDataset.from_list([{
        "user_input": question,
        "response": answer,
        "retrieved_contexts": retrieved_chunks,
    }])

    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy()],
        llm=_llm,
    )

    scores = {
        "faithfulness": float(result["faithfulness"]),
        "answer_relevancy": float(result["answer_relevancy"]),
    }

    trace_id = str(uuid.uuid4())
    _lf.trace(
        id=trace_id,
        name="ragas_generation_eval",
        input={"question": question, "retrieved_chunks": retrieved_chunks},
        output={"answer": answer, "scores": scores},
        tags=["ragas", "generation"],
    )
    _log_scores(trace_id, scores, "generation")

    return scores


if __name__ == "__main__":
    # --- sample smoke test ---
    sample_chunks = [
        "Led backend migration from monolith to microservices using Python and FastAPI.",
        "Designed and deployed REST APIs serving 50k daily active users.",
        "Proficient in PostgreSQL, Redis, and Docker-based deployments.",
    ]

    retrieval_scores = evaluate_retrieval(
        question="Python FastAPI microservices backend engineer",
        retrieved_chunks=sample_chunks,
        ground_truth="Candidate has experience building Python FastAPI microservices with PostgreSQL and Redis.",
    )
    print("Retrieval scores:", retrieval_scores)

    generation_scores = evaluate_generation(
        question="Tailor resume for a Senior Backend Engineer role requiring Python, FastAPI, and microservices.",
        answer="Architected microservices platform using FastAPI and PostgreSQL, reducing latency by 40%.",
        retrieved_chunks=sample_chunks,
    )
    print("Generation scores:", generation_scores)
    print("Hallucination risk:", "LOW" if generation_scores["faithfulness"] >= 0.8 else "HIGH")
