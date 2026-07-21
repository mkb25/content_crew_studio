from __future__ import annotations

from app.config import configure_local_paths

configure_local_paths()

CREWAI_IMPORT_ERROR: str | None = None

try:
    from crewai import Agent, Crew, LLM, Process, Task
except Exception as _crewai_err:  # pragma: no cover - exercised only before dependencies are installed
    Agent = Crew = LLM = Process = Task = None  # type: ignore[assignment]
    CREWAI_IMPORT_ERROR = f"{type(_crewai_err).__name__}: {_crewai_err}"

CREWAI_AVAILABLE = Crew is not None
