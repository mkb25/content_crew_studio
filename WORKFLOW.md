# Content Crew Studio Workflow

This document explains the full flow of Content Crew Studio, from the moment a user opens the Streamlit app to the moment the final edited content appears on screen.

## Overview

Content Crew Studio has two main parts:

- `streamlit_app.py`: the web interface, form handling, validation errors, theme toggle, and output rendering.
- `app/`: the reusable CrewAI workflow that creates agents, creates tasks, calls Groq, and returns the final content.

The workflow is intentionally linear:

```text
User brief
  -> Streamlit form
  -> Pydantic validation
  -> CrewAI setup checks
  -> Groq-backed LLM
  -> Research task
  -> Draft task
  -> Edit task
  -> Streamlit final output
```

## 1. App Startup

The app starts from `streamlit_app.py`:

```bash
streamlit run streamlit_app.py
```

When Streamlit imports the app, the workflow modules import configuration from `app/config.py`. That file does two important things:

1. Sets local XDG paths under `.local/`.
2. Loads environment variables from `.env`.

The local XDG paths keep CrewAI and LiteLLM cache/config files inside the project:

```text
.local/share
.local/config
.local/cache
```

These files are generated local state and should not be committed.

## 2. UI Rendering

`main()` in `streamlit_app.py` builds the page:

- Sets the browser page title and layout.
- Initializes the light/dark theme in `st.session_state`.
- Injects theme CSS.
- Renders the header.
- Renders the theme toggle.
- Renders two columns: input on the left, output on the right.

The input form collects:

- `topic`: what the content should be about.
- `style`: how the content should be written.
- `audience`: who the content is for.
- `length`: short, medium, or long.

The length labels map to internal values:

```python
LENGTH_OPTIONS = {
    "Short": "short",
    "Medium": "medium",
    "Long": "long",
}
```

Those internal values map to word-count guidance in `app/prompts.py`:

```text
short  -> 120 to 180 words
medium -> 350 to 550 words
long   -> 800 to 1200 words
```

## 3. Request Validation

When the user clicks `Run agents`, Streamlit calls `build_request()`.

That function creates a `GenerateRequest` from `app/schemas.py`:

```python
class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=240)
    style: str = Field(..., min_length=2, max_length=180)
    audience: str = Field(default="general readers", max_length=140)
    length: str = Field(default="medium", pattern="^(short|medium|long)$")
```

Validation protects the workflow from empty or oversized input. If validation fails, the app shows a Streamlit error and does not call CrewAI.

If the audience field is empty, the app falls back to:

```text
general readers
```

## 4. Generation Call

After validation succeeds, `run_generation()` calls:

```python
generate_with_content_crew(request)
```

This function lives in `app/crew_workflow.py` and is the main entry point for the backend workflow.

Before running the agents, it checks:

- CrewAI is installed.
- `GROQ_API_KEY` exists and is not a placeholder.
- The selected model name is available from the environment or default config.

If one of these checks fails, the workflow raises `AppError`. Streamlit catches that error and displays a readable message to the user.

## 5. Model Setup

The model name comes from:

1. `GROQ_MODEL` in `.env`, if set.
2. `DEFAULT_GROQ_MODEL` from `app/config.py`, if `GROQ_MODEL` is missing.

The default model is:

```text
llama-3.3-70b-versatile
```

CrewAI receives the model through LiteLLM using the Groq provider prefix:

```python
LLM(model=f"groq/{model_name}", temperature=0.7)
```

For example:

```text
groq/llama-3.3-70b-versatile
```

## 6. Agent Creation

`create_content_agents()` in `app/agents.py` creates three agents from profiles in `app/prompts.py`.

The agents are:

- Research Specialist
- Creative Draft Writer
- Senior Editor and Proofreader

Each agent receives the same Groq-backed LLM. Delegation is disabled, so the workflow stays predictable: each agent performs its assigned task only.

## 7. Task Creation

`create_content_tasks()` in `app/tasks.py` creates three tasks:

- `research`: creates a structured brief with explanation, key points, angles, questions, and caveats.
- `draft`: writes a complete draft from the research brief in the requested style.
- `edit`: proofreads and polishes the draft, returning only the final content.

The task context controls how information moves forward:

```text
research
  -> draft uses research
  -> edit uses research and draft
```

In code, the draft task receives:

```python
context=[research]
```

The edit task receives:

```python
context=[research, draft]
```

## 8. Crew Assembly

`build_content_crew()` wires everything together:

```python
Crew(
    agents=[agents.researcher, agents.writer, agents.editor],
    tasks=[tasks.research, tasks.draft, tasks.edit],
    process=Process.sequential,
    verbose=True,
)
```

`Process.sequential` is important. It means CrewAI runs the tasks in order:

1. Research
2. Draft
3. Edit

This makes the final content depend on the research and draft stages rather than asking one model call to do everything at once.

## 9. Crew Execution

The workflow starts with:

```python
crew.kickoff()
```

CrewAI then executes each task and passes task context forward. The final result is the editor's polished content.

`generate_with_content_crew()` returns two values:

```python
return str(result), model_name
```

Those values are:

- the final content as text.
- the model name used to generate it.

## 10. Output Rendering

Back in `streamlit_app.py`, `run_generation()` stores the result in Streamlit session state:

```python
st.session_state["generated_output"] = output
st.session_state["generated_model"] = model_name
```

Then the app reruns with:

```python
st.rerun()
```

On the next render, `render_output()` finds `generated_output` and displays:

- the final edited content.
- the model used.
- a `Download output` button that saves the content as `content-crew-output.md`.

Before rendering the content, the app escapes it with `html.escape()` because it is inserted into a custom HTML block.

## Error Flow

The app handles three broad error categories:

- Validation errors from Pydantic, shown beside the form.
- Expected app errors, such as missing CrewAI or missing `GROQ_API_KEY`.
- Unexpected provider/workflow errors from CrewAI, LiteLLM, Groq, or the network.

Expected errors use `AppError` from `app/errors.py`, which keeps user-facing error messages clean.

## Configuration Flow

The important environment variables are:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

`GROQ_API_KEY` is required. `GROQ_MODEL` is optional.

The app loads these values from `.env`, which should be created from `.env.example`:

```bash
cp .env.example .env
```

The `.env` file is ignored by Git because it contains secrets.

## End-To-End Sequence

1. User starts Streamlit.
2. App loads `.env` and configures local cache paths.
3. User enters topic, style, audience, and length.
4. User clicks `Run agents`.
5. Streamlit builds and validates a `GenerateRequest`.
6. Workflow checks CrewAI and Groq configuration.
7. Workflow creates the Groq-backed LLM.
8. Workflow creates researcher, writer, and editor agents.
9. Workflow creates research, draft, and edit tasks.
10. CrewAI runs the tasks sequentially.
11. The editor task returns the final polished content.
12. Streamlit stores the result in session state.
13. Streamlit rerenders and shows the final output.
14. User can download the output as Markdown.
