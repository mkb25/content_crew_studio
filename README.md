# Content Crew Studio

Content Crew Studio is a Streamlit app that uses a small CrewAI workflow to generate polished content from a simple brief. The user provides a topic, writing style, audience, and length. The app then runs three agents in sequence: researcher, draft writer, and editor.

## What It Does

- Collects a content brief in a Streamlit interface.
- Validates the request with Pydantic before running the workflow.
- Uses CrewAI with Groq as the LLM provider.
- Runs a sequential research, draft, and edit process.
- Displays the polished output in the app and lets you download it as Markdown.

## Project Structure

```text
content_crew_studio/
|-- app/
|   |-- agents.py          # Creates the CrewAI agents
|   |-- config.py          # Loads .env and configures local cache paths
|   |-- crewai_setup.py    # Imports CrewAI safely after local path setup
|   |-- crew_workflow.py   # Builds and runs the full crew
|   |-- errors.py          # App-specific error type
|   |-- prompts.py         # Agent profiles, task prompts, and length guidance
|   |-- schemas.py         # Pydantic request/response models
|   `-- tasks.py           # Creates the CrewAI tasks
|-- streamlit_app.py       # Streamlit UI and request handling
|-- requirements.txt       # Python dependencies
|-- .env.example           # Example environment variables
|-- WORKFLOW.md            # Detailed app flow
`-- CODE_WALKTHROUGH.md    # Code-oriented walkthrough
```

## Setup

```bash
cd content_crew_studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```bash
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

`GROQ_MODEL` is optional. If you remove it, the app uses `llama-3.3-70b-versatile`.

## Run

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Open the local URL Streamlit prints in the terminal. It is usually:

```text
http://localhost:8501
```

If port `8501` is busy:

```bash
streamlit run streamlit_app.py --server.port 8502
```

## Usage

1. Enter a topic, such as `AI agents for real estate sales`.
2. Enter a writing style, such as `a LinkedIn post`, `a stage play`, or `a horror story`.
3. Choose the target audience and output length.
4. Click `Run agents`.
5. Review the final edited output and download it if needed.

## Documentation

- [WORKFLOW.md](WORKFLOW.md) explains the full user-to-agent-to-output flow in detail.
- [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) explains the code modules and how they connect.

## Notes

- The app reads environment variables from `.env`.
- `.env` is ignored by Git so secrets are not committed.
- `.env.example` should only contain placeholders.
- CrewAI connects to Groq through model names like `groq/<model-name>`.
