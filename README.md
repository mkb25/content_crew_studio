# Content Crew Studio

Content Crew Studio is a simple Streamlit app that turns a short brief into polished content.

Enter a topic, audience, writing style, and length. The app sends the request through a CrewAI workflow where three agents research, draft, and edit the final piece.

## Features

- Streamlit web interface
- Light and dark mode
- Three-step agent workflow
- Groq-powered content generation
- Copy and Markdown download for the final output

## Quick Start

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
touch .env
```

Add your Groq API key to `.env`:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Run the app:

```bash
streamlit run streamlit_app.py
```

Open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

If the port is busy, choose another one:

```bash
streamlit run streamlit_app.py --server.port 8502
```

## How It Works

The workflow runs in this order:

1. **Researcher** finds useful facts, angles, and audience context.
2. **Writer** creates a draft in the requested style.
3. **Editor** improves clarity, flow, and polish.

The edited result appears in the final output panel, ready to copy or download.

## Main Files

```text
streamlit_app.py       App UI and page behavior
app/prompts.py         Agent profiles and task prompts
app/agents.py          CrewAI agent setup
app/tasks.py           CrewAI task setup
app/crew_workflow.py   Workflow orchestration
app/schemas.py         Request validation
requirements.txt       Python dependencies
```

## More Docs

- [WORKFLOW.md](WORKFLOW.md): detailed app flow
- [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md): code-level walkthrough

## Notes

- Keep real secrets in `.env`.
- Do not commit `.env` or `.venv`.
