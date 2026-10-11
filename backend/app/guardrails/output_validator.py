from app.agents.state import AgentState
from app.websocket.manager import manager
from langfuse import observe

_PLACEHOLDERS = {"INSERT", "TODO", "PLACEHOLDER"}


def _has_placeholder(text: str) -> bool:
    upper = text.upper()
    return any(p in upper for p in _PLACEHOLDERS)


def _strip_fences(text: str) -> str:
    """Strip markdown code fences that free LLMs add despite instructions."""
    import re
    return re.sub(r"^```[\w]*\n?", "", re.sub(r"\n?```$", "", text.strip())).strip()


def _validate(state: AgentState) -> list[str]:
    errors: list[str] = []

    # --- parsed_jd ---
    parsed_jd = state.get("parsed_jd") or {}
    if not parsed_jd.get("company_name"):
        errors.append("parsed_jd: company_name is empty")
    if not parsed_jd.get("role_title"):
        errors.append("parsed_jd: role_title is empty")
    if not parsed_jd.get("required_skills"):
        errors.append("parsed_jd: required_skills is empty")

    # --- tailored_resume_latex ---
    latex = _strip_fences(state.get("tailored_resume_latex") or "")
    if not latex:
        errors.append("tailored_resume_latex: missing")
    else:
        if r"\begin{document}" not in latex and "\\begin{document}" not in latex:
            errors.append("tailored_resume_latex: missing \\begin{document}")
        if _has_placeholder(latex):
            errors.append("tailored_resume_latex: contains placeholder text")

    # --- cover_letter ---
    cover_letter = state.get("cover_letter") or ""
    if not cover_letter:
        errors.append("cover_letter: missing")
    else:
        word_count = len(cover_letter.split())
        if word_count < 50:
            errors.append(f"cover_letter: too short ({word_count} words, minimum 50)")
        if word_count > 800:
            errors.append(f"cover_letter: too long ({word_count} words, maximum 800)")
        if _has_placeholder(cover_letter):
            errors.append("cover_letter: contains placeholder text")

    # --- interview_questions ---
    questions = state.get("interview_questions") or []
    if not questions:
        errors.append("interview_questions: missing")
    else:
        if len(questions) < 5:
            errors.append(f"interview_questions: expected at least 5, got {len(questions)}")
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                errors.append(f"interview_questions[{i}]: not a dict")
                continue
            if not q.get("question"):
                errors.append(f"interview_questions[{i}]: missing question")

    return errors


@observe(name="guardrails", as_type="agent")
async def guardrails_agent(state: AgentState) -> AgentState:
    job_id = state["job_id"]

    await manager.send_progress(job_id, {
        "agent": "guardrails",
        "status": "started",
        "message": "Validating outputs...",
    })

    errors = _validate(state)
    passed = len(errors) == 0

    await manager.send_progress(job_id, {
        "agent": "guardrails",
        "status": "completed" if passed else "failed",
        "message": "Validation passed." if passed else f"Validation failed: {len(errors)} error(s).",
        "errors": errors,
    })

    result = {
        "validation_passed": passed,
        "validation_errors": errors,
        "current_agent": "guardrails",
        "completed_agents": ["guardrails"],
    }
    if not passed:
        result["error"] = f"Validation failed: {'; '.join(errors)}"
    return result
