from __future__ import annotations

from dataclasses import dataclass

from app.agents import ContentAgents
from app.crewai_setup import Task
from app.prompts import (
    DRAFT_TASK_DESCRIPTION,
    EDIT_TASK_DESCRIPTION,
    LENGTH_GUIDANCE,
    RESEARCH_TASK_DESCRIPTION,
)
from app.schemas import GenerateRequest


@dataclass(frozen=True)
class ContentTasks:
    research: Task
    draft: Task
    edit: Task


def create_content_tasks(agents: ContentAgents, request: GenerateRequest) -> ContentTasks:
    research = Task(
        description=RESEARCH_TASK_DESCRIPTION.format(
            topic=request.topic,
            audience=request.audience,
            style=request.style,
            length_guidance=LENGTH_GUIDANCE[request.length],
        ),
        expected_output="A structured research brief with facts, angles, and caveats.",
        agent=agents.researcher,
    )

    draft = Task(
        description=DRAFT_TASK_DESCRIPTION.format(
            length_guidance=LENGTH_GUIDANCE[request.length],
            topic=request.topic,
            audience=request.audience,
            style=request.style,
        ),
        expected_output="A complete draft in the requested style.",
        agent=agents.writer,
        context=[research],
    )

    edit = Task(
        description=EDIT_TASK_DESCRIPTION.format(
            style=request.style,
            length_guidance=LENGTH_GUIDANCE[request.length],
        ),
        expected_output="The final polished content only.",
        agent=agents.editor,
        context=[research, draft],
    )

    return ContentTasks(research=research, draft=draft, edit=edit)
