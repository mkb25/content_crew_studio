from __future__ import annotations

from dataclasses import dataclass

from app.crewai_setup import Agent, LLM
from app.prompts import AGENT_PROFILES


@dataclass(frozen=True)
class ContentAgents:
    researcher: Agent
    writer: Agent
    editor: Agent


def create_content_agents(llm: LLM) -> ContentAgents:
    return ContentAgents(
        researcher=create_agent("researcher", llm),
        writer=create_agent("writer", llm),
        editor=create_agent("editor", llm),
    )


def create_agent(profile_name: str, llm: LLM) -> Agent:
    profile = AGENT_PROFILES[profile_name]
    return Agent(
        role=profile["role"],
        goal=profile["goal"],
        backstory=profile["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

