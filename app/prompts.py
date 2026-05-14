from __future__ import annotations

LENGTH_GUIDANCE = {
    "short": "120 to 180 words",
    "medium": "350 to 550 words",
    "long": "800 to 1200 words",
}

AGENT_PROFILES = {
    "researcher": {
        "role": "Research Specialist",
        "goal": "Find useful, accurate, and audience-relevant information for a content brief.",
        "backstory": (
            "You are a sharp content researcher who distills noisy topics into clear angles, "
            "key facts, audience concerns, and practical context."
        ),
    },
    "writer": {
        "role": "Creative Draft Writer",
        "goal": "Turn research into an engaging draft that exactly follows the requested style.",
        "backstory": (
            "You are a versatile marketing and editorial writer who can write explainers, "
            "plays, horror stories, founder notes, newsletters, scripts, and campaign copy."
        ),
    },
    "editor": {
        "role": "Senior Editor and Proofreader",
        "goal": "Improve clarity, structure, grammar, style consistency, and final polish.",
        "backstory": (
            "You are a careful editor who protects the user's requested voice while making "
            "the piece cleaner, more coherent, and ready to publish."
        ),
    },
}

RESEARCH_TASK_DESCRIPTION = (
    "Research the topic: '{topic}'. Audience: '{audience}'. "
    "The final piece must be written in this style or framing: '{style}'. "
    "Create a concise research brief with: core explanation, 3-5 key points, "
    "interesting angles, likely audience questions, and important caveats. "
    "Keep the brief compact because the final output length is {length_guidance}."
)

DRAFT_TASK_DESCRIPTION = (
    "Using the research brief, write a {length_guidance} draft about '{topic}' "
    "for '{audience}'. The writing must follow this requested style: '{style}'. "
    "Stay within {length_guidance}. Make it vivid and useful, but do not expand "
    "beyond the requested length. Avoid unsupported claims and keep the structure easy to read."
)

EDIT_TASK_DESCRIPTION = (
    "Edit and proofread the draft. Preserve the requested style: '{style}'. "
    "The final answer must be {length_guidance}; if the draft is longer, compress it. "
    "Improve grammar, flow, factual caution, transitions, and ending. "
    "Return only the final polished content, without editor notes."
)
