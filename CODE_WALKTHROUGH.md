# Content Crew Studio Code Walkthrough

This document explains how the Streamlit version of Content Crew Studio works.

## High-Level Architecture

Content Crew Studio now has two main layers:

- `streamlit_app.py`: the user interface.
- `app/`: the reusable CrewAI workflow code.

Streamlit collects the user's topic, style, audience, and length. It then builds a `GenerateRequest` and calls the same CrewAI workflow directly. There is no separate HTML, JavaScript, or FastAPI server in the current version.

## File Structure

```text
content_crew_studio/
|-- app/
|   |-- __init__.py
|   |-- agents.py
|   |-- config.py
|   |-- crewai_setup.py
|   |-- crew_workflow.py
|   |-- errors.py
|   |-- prompts.py
|   |-- schemas.py
|   `-- tasks.py
|-- .env
|-- .env.example
|-- README.md
|-- CODE_WALKTHROUGH.md
|-- requirements.txt
`-- streamlit_app.py
```

## Streamlit UI

The app starts in `streamlit_app.py`.

```python
def main() -> None:
    st.set_page_config(...)
```

The UI uses a two-column layout: the left column collects the content brief, and the right column shows the generated output.

The form collects:

- Topic
- Requested writing style
- Audience
- Length

When the user clicks `Run agents`, Streamlit calls:

```python
request = build_request(...)
run_generation(request)
```

## Request Validation

The request shape lives in `app/schemas.py`.

```python
class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=240)
    style: str = Field(..., min_length=2, max_length=180)
    audience: str = Field(default="general readers", max_length=140)
    length: str = Field(default="medium", pattern="^(short|medium|long)$")
```

`streamlit_app.py` uses this model before running the agents. If the user submits an invalid value, Streamlit shows the validation error instead of starting the workflow.

## Configuration

Configuration lives in `app/config.py`.

Important values:

```python
BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DIR = BASE_DIR / ".local"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
```

The app also sets local XDG paths:

```python
os.environ.setdefault("XDG_DATA_HOME", str(LOCAL_DIR / "share"))
os.environ.setdefault("XDG_CONFIG_HOME", str(LOCAL_DIR / "config"))
os.environ.setdefault("XDG_CACHE_HOME", str(LOCAL_DIR / "cache"))
```

This keeps CrewAI and LiteLLM cache/config writes inside the project instead of the user's home directory.

The `.env` file is loaded by `config.py`:

```python
load_dotenv(BASE_DIR / ".env")
```

Expected environment variables:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

`GROQ_MODEL` is optional. If it is missing, the app uses `DEFAULT_GROQ_MODEL`.

## CrewAI Modules

The CrewAI logic is split across small files:

- `crewai_setup.py`: imports CrewAI after local paths are configured.
- `prompts.py`: stores agent profiles, task prompt templates, and length guidance.
- `agents.py`: builds the researcher, writer, and editor agents.
- `tasks.py`: builds the research, draft, and edit tasks.
- `crew_workflow.py`: validates setup, creates the LLM, wires agents/tasks together, and runs the crew.
- `errors.py`: defines `AppError`, which the Streamlit UI can display cleanly.

## Prompt Text

Prompt-heavy content lives in `app/prompts.py`.

The app currently uses these output length targets:

```python
LENGTH_GUIDANCE = {
    "short": "120 to 180 words",
    "medium": "350 to 550 words",
    "long": "800 to 1200 words",
}
```

Agent identity is stored in `AGENT_PROFILES`, and task instructions are stored as string templates. Keeping this text in one file makes it easier to adjust the behavior without digging through workflow code.

## Agent Creation

Agents are created in `app/agents.py`.

```python
def create_content_agents(llm: LLM) -> ContentAgents:
    return ContentAgents(
        researcher=create_agent("researcher", llm),
        writer=create_agent("writer", llm),
        editor=create_agent("editor", llm),
    )
```

The three agents are:

- Research Specialist
- Creative Draft Writer
- Senior Editor and Proofreader

The `ContentAgents` dataclass gives each agent a clear name.

## Task Creation

Tasks are created in `app/tasks.py`.

```python
def create_content_tasks(agents: ContentAgents, request: GenerateRequest) -> ContentTasks:
```

The workflow uses three sequential tasks:

- `research`: builds a compact research brief.
- `draft`: writes the first version using the research task as context.
- `edit`: polishes and compresses the final output using both earlier tasks as context.

The draft task depends on the research task:

```python
context=[research]
```

The edit task depends on both earlier tasks:

```python
context=[research, draft]
```

## Workflow Execution

The main workflow entry point is in `app/crew_workflow.py`.

```python
def generate_with_content_crew(request: GenerateRequest) -> tuple[str, str]:
```

It does five things:

1. Checks that CrewAI is installed.
2. Checks that `GROQ_API_KEY` exists.
3. Creates a Groq-backed CrewAI LLM.
4. Builds the three-agent content crew.
5. Runs the workflow and returns the final text plus the model name.

The LLM is created like this:

```python
llm = LLM(model=f"groq/{model_name}", temperature=0.7)
```

CrewAI/LiteLLM expects Groq model names to be prefixed with `groq/`.

The final crew is built like this:

```python
return Crew(
    agents=[agents.researcher, agents.writer, agents.editor],
    tasks=[tasks.research, tasks.draft, tasks.edit],
    process=Process.sequential,
    verbose=True,
)
```

`Process.sequential` means the tasks run in order:

1. Research
2. Draft
3. Edit

The workflow is executed with:

```python
result = crew.kickoff()
```

## Error Handling

Application-level errors use `AppError` from `app/errors.py`.

Examples:

- CrewAI is not installed.
- `GROQ_API_KEY` is missing.
- The Groq/CrewAI workflow fails.

`streamlit_app.py` catches `AppError` and displays the message with:

```python
st.error(exc.detail)
```

## End-To-End Lifecycle

Here is the full flow:

1. User runs `streamlit run streamlit_app.py`.
2. Streamlit opens the app in the browser.
3. User fills out topic, style, audience, and length.
4. Streamlit validates the values with `GenerateRequest`.
5. `run_generation()` calls `generate_with_content_crew()`.
6. The workflow validates dependencies and the Groq key.
7. The workflow creates the Groq-backed LLM.
8. The workflow creates agents and tasks.
9. CrewAI runs research, draft, and edit in order.
10. Streamlit displays the final output and offers a download button.

## How To Run

From the project root:

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Streamlit prints the browser URL in the terminal. It usually uses:

```text
http://localhost:8501
```

If port `8501` is already busy, run:

```bash
streamlit run streamlit_app.py --server.port 8502
```

Then open:

```text
http://localhost:8502
```

## How To Test Quickly

Check imports:

```bash
.venv/bin/python -c "from streamlit_app import main; print(main.__name__)"
```

Compile the Python files:

```bash
.venv/bin/python -m compileall app streamlit_app.py
```
