from __future__ import annotations

from app.config import configure_local_paths

configure_local_paths()

try:
    from crewai import Agent, Crew, LLM, Process, Task
except ImportError:  # pragma: no cover - exercised only before dependencies are installed
    Agent = Crew = LLM = Process = Task = None

CREWAI_AVAILABLE = Crew is not None
