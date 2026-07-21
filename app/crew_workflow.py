from __future__ import annotations

import os

from app.agents import create_content_agents
from app.config import DEFAULT_GROQ_MODEL, PLACEHOLDER_GROQ_KEYS
from app.crewai_setup import CREWAI_AVAILABLE, CREWAI_IMPORT_ERROR, Crew, LLM, Process
from app.errors import AppError
from app.schemas import GenerateRequest
from app.tasks import create_content_tasks


def generate_with_content_crew(request: GenerateRequest) -> tuple[str, str]:
    ensure_crewai_installed()
    validate_groq_key()

    model_name = get_model_name()
    llm = LLM(model=f"groq/{model_name}", temperature=0.7)
    crew = build_content_crew(llm, request)

    try:
        result = crew.kickoff()
    except Exception as exc:  # pragma: no cover - depends on provider/network behavior
        raise AppError(f"Agent workflow failed: {exc}") from exc

    return str(result), model_name


def ensure_crewai_installed() -> None:
    if not CREWAI_AVAILABLE:
        detail = CREWAI_IMPORT_ERROR or "unknown import error"
        raise AppError(
            f"CrewAI failed to load: {detail}\n\n"
            "Run `python3.12-64.exe -m pip install --prefer-binary -r requirements.txt` "
            "and restart the app."
        )


def validate_groq_key() -> None:
    api_key = os.getenv("GROQ_API_KEY", "").strip().strip("'\"")
    if api_key in PLACEHOLDER_GROQ_KEYS:
        raise AppError("Missing GROQ_API_KEY. Add it to content_crew_studio/.env.")


def get_model_name() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip().strip("'\"") or DEFAULT_GROQ_MODEL


def build_content_crew(llm: LLM, request: GenerateRequest) -> Crew:
    agents = create_content_agents(llm)
    tasks = create_content_tasks(agents, request)

    return Crew(
        agents=[agents.researcher, agents.writer, agents.editor],
        tasks=[tasks.research, tasks.draft, tasks.edit],
        process=Process.sequential,
        verbose=True,
    )
