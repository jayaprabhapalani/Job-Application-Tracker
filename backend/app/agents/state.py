from typing import Annotated, Any, TypedDict


def _last(a, b):
    return b

def _extend(a, b):
    return (a or []) + (b or [])


class AgentState(TypedDict):
    # Inputs
    job_id: Annotated[str, _last]
    user_id: Annotated[str, _last]
    jd_text: Annotated[str, _last]
    company: Annotated[str, _last]
    role: Annotated[str, _last]

    # Agent outputs
    parsed_jd: Annotated[dict, _last]
    company_research: Annotated[str, _last]
    interview_questions: Annotated[list, _last]
    tailored_resume_latex: Annotated[str, _last]
    cover_letter: Annotated[str, _last]

    # Guardrails
    validation_passed: Annotated[bool, _last]
    validation_errors: Annotated[list, _last]

    # Progress tracking
    completed_agents: Annotated[list, _extend]
    current_agent: Annotated[str, _last]

    # Error tracking
    error: Annotated[str, _last]

    # Internal — session factory passed through pipeline
    _session_factory: Annotated[Any, _last]
