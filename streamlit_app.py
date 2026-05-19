from __future__ import annotations

import html
import json
import os
import re
from urllib.parse import quote

from pydantic import ValidationError
import streamlit as st
import streamlit.components.v1 as components

from app.crew_workflow import generate_with_content_crew
from app.errors import AppError
from app.schemas import GenerateRequest


LENGTH_OPTIONS = {
    "Short": "short",
    "Medium": "medium",
    "Long": "long",
}

# Available Groq models (add or adjust as needed)
MODEL_OPTIONS = {
    "llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b": "openai/gpt-oss-120b",
    "groq/compound-mini": "groq/compound-mini",
}

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+|mailto:[^)\s]+)\)")

THEME_TOKENS = {
    "Light": {
        "background": "#f7f8fa",
        "panel": "#ffffff",
        "panel_alt": "#f1f4f7",
        "text": "#1f2933",
        "muted": "#697586",
        "border": "#d7dde4",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_soft": "#eef4ff",
        "accent_text": "#ffffff",
        "input": "#ffffff",
        "output": "#ffffff",
        "shadow": "0 10px 28px rgba(31, 41, 51, 0.08)",
    },
    "Dark": {
        "background": "#111418",
        "panel": "#171b21",
        "panel_alt": "#1f252d",
        "text": "#f4f6f8",
        "muted": "#9ca7b4",
        "border": "#303844",
        "accent": "#60a5fa",
        "accent_hover": "#93c5fd",
        "accent_soft": "#172842",
        "accent_text": "#0b1220",
        "input": "#11161c",
        "output": "#11161c",
        "shadow": "0 12px 34px rgba(0, 0, 0, 0.32)",
    },
}


def main() -> None:
    st.set_page_config(
        page_title="Content Crew Studio",
        page_icon="CC",
        layout="wide",
    )

    theme = get_theme()
    inject_theme_css(theme)
    render_top_bar(theme)

    input_column, output_column = st.columns([0.95, 1.55], gap="large")

    with input_column:
        render_compose_panel()

    with output_column:
        render_output()


def get_theme() -> str:
    if "theme" not in st.session_state:
        st.session_state["theme"] = "Light"

    return st.session_state["theme"]


def render_top_bar(theme: str) -> None:
    header_column, theme_column = st.columns([3.2, 1], gap="large")
    with header_column:
        render_header()
    with theme_column:
        render_theme_toggle(theme)


def render_theme_toggle(theme: str) -> None:
    st.markdown('<div class="theme-label">Appearance</div>', unsafe_allow_html=True)
    next_theme = "Dark" if theme == "Light" else "Light"
    if st.button(f"{next_theme} mode", key="theme_toggle"):
        st.session_state["theme"] = next_theme
        st.rerun()


def render_compose_panel() -> None:
    render_section_heading("Compose", "Brief the crew")
    form_values = render_compose_form()

    if form_values is None:
        return

    topic, style, audience, length_label, model_label = form_values
    request = build_request(
        topic=topic,
        style=style,
        audience=audience,
        length=LENGTH_OPTIONS[length_label],
    )
    if request is None:
        return

    os.environ["GROQ_MODEL"] = MODEL_OPTIONS[model_label]
    prepare_generation_run(request)
    run_generation(request)


def render_section_heading(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading">
          <span>{html.escape(title)}</span>
          <small>{html.escape(subtitle)}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_compose_form() -> tuple[str, str, str, str, str] | None:
    with st.form("content-form"):
        topic = st.text_input(
            "Topic",
            placeholder="Example: AI agents for real estate sales",
            max_chars=240,
        )
        style = st.text_input(
            "Write it like",
            placeholder="Example: a horror story, a stage play, a LinkedIn post",
            max_chars=180,
        )
        audience_column, length_column = st.columns([1, 1], gap="medium")
        with audience_column:
            audience = st.text_input("Audience", value="marketing leaders", max_chars=140)
        with length_column:
            length_label = st.selectbox(
                "Length",
                options=list(LENGTH_OPTIONS),
                format_func=format_length_option,
                index=1,
            )

        model_label = st.selectbox(
            "Model",
            options=list(MODEL_OPTIONS),
            index=0,
        )
        submitted = st.form_submit_button("Run agents", type="primary")

    if not submitted:
        return None

    return topic, style, audience, length_label, model_label


def prepare_generation_run(request: GenerateRequest) -> None:
    st.session_state["last_request"] = request
    st.session_state.pop("generated_output", None)
    st.session_state.pop("generated_model", None)


def inject_theme_css(theme: str) -> None:
    tokens = THEME_TOKENS[theme]
    st.markdown(
        f"""
        <style>
          :root {{
            --cc-bg: {tokens["background"]};
            --cc-panel: {tokens["panel"]};
            --cc-panel-alt: {tokens["panel_alt"]};
            --cc-text: {tokens["text"]};
            --cc-muted: {tokens["muted"]};
            --cc-border: {tokens["border"]};
            --cc-accent: {tokens["accent"]};
            --cc-accent-hover: {tokens["accent_hover"]};
            --cc-accent-soft: {tokens["accent_soft"]};
            --cc-accent-text: {tokens["accent_text"]};
            --cc-input: {tokens["input"]};
            --cc-output: {tokens["output"]};
            --cc-shadow: {tokens["shadow"]};
          }}

          .stApp {{
            background: var(--cc-bg);
            color: var(--cc-text);
          }}

          .block-container {{
            max-width: 1320px;
            padding-top: 1.65rem;
            padding-bottom: 2.5rem;
          }}

          [data-testid="stSidebar"] {{
            display: none;
          }}

          .app-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            min-height: 4rem;
          }}

          .brand-mark {{
            display: inline-flex;
            width: 2.35rem;
            height: 2.35rem;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: var(--cc-accent);
            color: var(--cc-accent-text);
            font-weight: 850;
            letter-spacing: 0;
          }}

          .app-title h1 {{
            margin: 0;
            color: var(--cc-text);
            font-size: 1.38rem;
            line-height: 1.1;
          }}

          .app-title p {{
            margin: 0.22rem 0 0;
            color: var(--cc-muted);
            font-size: 0.9rem;
          }}

          .theme-label {{
            color: var(--cc-muted);
            font-size: 0.78rem;
            font-weight: 750;
            margin: 0 0 0.25rem;
            text-align: right;
          }}

          .section-heading {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin: 1.15rem 0 0.55rem;
          }}

          .section-heading span {{
            color: var(--cc-text);
            font-size: 1.08rem;
            font-weight: 800;
          }}

          .section-heading small {{
            color: var(--cc-muted);
            font-size: 0.86rem;
          }}

          [data-testid="stForm"], .output-pane {{
            background: var(--cc-panel);
            border: 1px solid var(--cc-border);
            border-radius: 8px;
            box-shadow: var(--cc-shadow);
            padding: 1.15rem;
          }}

          [data-testid="stForm"] label,
          [data-testid="stForm"] p,
          [data-testid="stForm"] span,
          [data-testid="stSelectbox"] label,
          .output-pane,
          .output-pane * {{
            color: var(--cc-text);
          }}

          [data-testid="stForm"] label,
          [data-testid="stSelectbox"] label {{
            font-weight: 750;
          }}

          .stTextInput input,
          .stSelectbox div[data-baseweb="select"] > div {{
            background-color: var(--cc-input);
            color: var(--cc-text);
            border-color: var(--cc-border);
            border-radius: 6px;
          }}

          .stTextInput input {{
            min-height: 3rem;
          }}

          .stTextInput input:focus {{
            border-color: var(--cc-accent);
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--cc-accent) 20%, transparent);
          }}

          [data-testid="InputInstructions"] {{
            display: none;
          }}

          .stFormSubmitButton > button,
          .stDownloadButton > button {{
            width: 100%;
            min-height: 3rem;
            border-radius: 6px;
            border: 1px solid var(--cc-accent);
            background: var(--cc-accent);
            color: var(--cc-accent-text);
            font-weight: 800;
            box-shadow: none;
          }}

          .stButton > button:hover,
          .stFormSubmitButton > button:hover,
          .stDownloadButton > button:hover {{
            border-color: var(--cc-accent-hover);
            background: var(--cc-accent-hover);
            color: var(--cc-accent-text);
          }}

          .stButton > button {{
            width: 100%;
            min-height: 2.35rem;
            border-radius: 6px;
            border: 1px solid var(--cc-border);
            background: var(--cc-panel);
            color: var(--cc-text);
            font-weight: 750;
            box-shadow: none;
          }}

          .stButton > button:hover {{
            border-color: var(--cc-accent);
            background: var(--cc-panel-alt);
            color: var(--cc-text);
          }}

          .stDownloadButton {{
            margin-top: 0.75rem;
          }}

          .output-header {{
            display: flex;
            align-items: start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
          }}

          .output-header h2 {{
            margin: 0;
            color: var(--cc-text);
            font-size: 1.25rem;
          }}

          .status-text {{
            margin: 0.2rem 0 0;
            color: var(--cc-muted);
            font-size: 0.92rem;
          }}

          .output-body {{
            min-height: 428px;
            border: 1px solid var(--cc-border);
            border-radius: 6px;
            background: var(--cc-output);
            padding: 1.15rem;
            color: var(--cc-text);
            line-height: 1.6;
            white-space: pre-wrap;
          }}

          .empty-output {{
            color: var(--cc-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
          }}

          [data-testid="stAlert"] {{
            border-radius: 6px;
          }}

          @media (max-width: 760px) {{
            .app-header {{
              align-items: flex-start;
            }}

            .theme-label {{
              text-align: left;
            }}

          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
          <div class="brand-mark">CC</div>
          <div class="app-title">
            <h1>Content Crew Studio</h1>
            <p>Research, draft, and edit content with a focused agent workflow.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_length_option(label: str) -> str:
    return label


def build_request(
    topic: str,
    style: str,
    audience: str,
    length: str,
) -> GenerateRequest | None:
    try:
        return GenerateRequest(
            topic=topic.strip(),
            style=style.strip(),
            audience=audience.strip() or "general readers",
            length=length,
        )
    except ValidationError as exc:
        st.error(exc.errors()[0]["msg"])
        return None


def run_generation(request: GenerateRequest) -> None:
    with st.spinner("The researcher, writer, and editor are working..."):
        try:
            output, model_name = generate_with_content_crew(request)
        except AppError as exc:
            render_generation_error(exc.detail)
            return
        except Exception as exc:  # pragma: no cover - depends on provider/network behavior
            render_generation_error(str(exc))
            return

    st.session_state["generated_output"] = output
    st.session_state["generated_model"] = model_name
    st.session_state["generation_run_id"] = st.session_state.get("generation_run_id", 0) + 1


def render_generation_error(detail: str) -> None:
    st.error(get_friendly_error_message(detail))

    cleaned_detail = detail.strip()
    if cleaned_detail:
        with st.expander("Technical details"):
            st.code(truncate_error_detail(cleaned_detail), language="text")


def get_friendly_error_message(detail: str) -> str:
    normalized = detail.lower()

    if "missing groq_api_key" in normalized or "api key" in normalized and "missing" in normalized:
        return "Missing Groq API key. Add `GROQ_API_KEY` to your `.env` file and try again."

    if "authentication" in normalized or "invalid api key" in normalized or "401" in normalized:
        return "Groq rejected the API key. Check that `GROQ_API_KEY` is valid, then run the agents again."

    if "rate limit" in normalized or "429" in normalized:
        return "The model provider is rate limiting requests right now. Wait a moment, then try again."

    if "quota" in normalized or "insufficient" in normalized and "credits" in normalized:
        return "The model provider reported a quota or credits issue. Check the Groq account limits and billing."

    if "model" in normalized and (
        "not found" in normalized
        or "does not exist" in normalized
        or "decommissioned" in normalized
        or "unsupported" in normalized
    ):
        return "The selected model is unavailable. Choose another model and run the agents again."

    if "timeout" in normalized or "timed out" in normalized:
        return "The agent workflow took too long to respond. Try again with a shorter brief or a different model."

    if "connection" in normalized or "network" in normalized or "dns" in normalized:
        return "The app could not reach the model provider. Check the network connection and try again."

    if "crewai is not installed" in normalized:
        return "CrewAI is not installed. Run `pip install -r requirements.txt`, then restart the app."

    return "The agent workflow could not finish. Please try again or switch models."


def truncate_error_detail(detail: str, limit: int = 1600) -> str:
    single_spaced = re.sub(r"\n{3,}", "\n\n", detail)
    if len(single_spaced) <= limit:
        return single_spaced

    return f"{single_spaced[:limit].rstrip()}\n\n... technical details truncated ..."


def render_output() -> None:
    output = st.session_state.get("generated_output")
    if not output:
        st.markdown(
            """
            <div class="output-pane">
              <div class="output-header">
                <div>
                  <h2>Final Output</h2>
                  <p class="status-text">Ready for a topic.</p>
                </div>
              </div>
              <div class="output-body empty-output">Your edited content will appear here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    render_generated_output(
        output=output,
        model_name=st.session_state["generated_model"],
        theme=st.session_state["theme"],
        run_id=st.session_state.get("generation_run_id", 0),
    )


def markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []
    code_lines: list[str] = []
    code_language = ""
    in_code_block = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            rendered = " ".join(render_inline_markdown(line.strip()) for line in paragraph)
            blocks.append(f"<p>{rendered}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_type, list_items
        if list_type and list_items:
            items = "".join(f"<li>{item}</li>" for item in list_items)
            blocks.append(f"<{list_type}>{items}</{list_type}>")
        list_type = None
        list_items = []

    line_index = 0
    while line_index < len(lines):
        raw_line = lines[line_index]
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code_block:
                language_class = f' class="language-{html.escape(code_language)}"' if code_language else ""
                code = html.escape("\n".join(code_lines))
                blocks.append(f"<pre><code{language_class}>{code}</code></pre>")
                code_lines = []
                code_language = ""
                in_code_block = False
            else:
                flush_paragraph()
                flush_list()
                code_language = stripped[3:].strip().split(maxsplit=1)[0]
                in_code_block = True
            line_index += 1
            continue

        if in_code_block:
            code_lines.append(line)
            line_index += 1
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            line_index += 1
            continue

        if line_index + 1 < len(lines) and is_table_separator_row(lines[line_index + 1]):
            header_cells = split_markdown_table_row(line)
            alignments = parse_table_alignments(lines[line_index + 1])
            if len(header_cells) >= 2 and len(header_cells) == len(alignments):
                flush_paragraph()
                flush_list()
                table_rows: list[list[str]] = []
                line_index += 2
                while line_index < len(lines):
                    row_line = lines[line_index].strip()
                    row_cells = split_markdown_table_row(row_line)
                    if not row_line or len(row_cells) != len(header_cells):
                        break
                    table_rows.append(row_cells)
                    line_index += 1

                blocks.append(render_markdown_table(header_cells, alignments, table_rows))
                continue

        if is_table_separator_row(line):
            line_index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{render_inline_markdown(heading.group(2))}</h{level}>")
            line_index += 1
            continue

        quote_match = re.match(r"^>\s?(.+)$", stripped)
        if quote_match:
            flush_paragraph()
            flush_list()
            blocks.append(f"<blockquote>{render_inline_markdown(quote_match.group(1))}</blockquote>")
            line_index += 1
            continue

        unordered = re.match(r"^[-*+]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            current_type = "ul" if unordered else "ol"
            if list_type and list_type != current_type:
                flush_list()
            list_type = current_type
            item_text = unordered.group(1) if unordered else ordered.group(1)
            list_items.append(render_inline_markdown(item_text))
            line_index += 1
            continue

        flush_list()
        paragraph.append(stripped)
        line_index += 1

    if in_code_block:
        language_class = f' class="language-{html.escape(code_language)}"' if code_language else ""
        code = html.escape("\n".join(code_lines))
        blocks.append(f"<pre><code{language_class}>{code}</code></pre>")

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def split_markdown_table_row(row: str) -> list[str]:
    stripped = row.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    return [cell.strip() for cell in stripped.split("|")]


def is_table_separator_row(row: str) -> bool:
    cells = split_markdown_table_row(row)
    if len(cells) < 2:
        return False

    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def parse_table_alignments(separator_row: str) -> list[str]:
    alignments: list[str] = []
    for cell in split_markdown_table_row(separator_row):
        stripped = cell.strip()
        if stripped.startswith(":") and stripped.endswith(":"):
            alignments.append("center")
        elif stripped.endswith(":"):
            alignments.append("right")
        else:
            alignments.append("left")

    return alignments


def render_markdown_table(
    header_cells: list[str],
    alignments: list[str],
    body_rows: list[list[str]],
) -> str:
    header_html = "".join(
        render_table_cell("th", cell, alignments[index])
        for index, cell in enumerate(header_cells)
    )
    rows_html = "".join(
        "<tr>"
        + "".join(render_table_cell("td", cell, alignments[index]) for index, cell in enumerate(row))
        + "</tr>"
        for row in body_rows
    )

    return (
        '<div class="table-wrap">'
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
        "</div>"
    )


def render_table_cell(tag: str, cell: str, alignment: str) -> str:
    return f'<{tag} style="text-align: {alignment};">{render_inline_markdown(cell)}</{tag}>'


def render_inline_markdown(text: str) -> str:
    parts = INLINE_CODE_RE.split(text)
    rendered_parts: list[str] = []

    for index, part in enumerate(parts):
        if index % 2:
            rendered_parts.append(f"<code>{html.escape(part)}</code>")
            continue

        link_position = 0
        rendered_segment: list[str] = []
        for match in LINK_RE.finditer(part):
            rendered_segment.append(render_emphasis(html.escape(part[link_position:match.start()])))
            href = html.escape(match.group(2), quote=True)
            label = render_emphasis(html.escape(match.group(1)))
            rendered_segment.append(
                f'<a href="{href}" target="_blank" rel="noopener noreferrer">{label}</a>'
            )
            link_position = match.end()
        rendered_segment.append(render_emphasis(html.escape(part[link_position:])))
        rendered_parts.append("".join(rendered_segment))

    return "".join(rendered_parts)


def render_emphasis(escaped_text: str) -> str:
    escaped_text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped_text)
    escaped_text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", escaped_text)
    escaped_text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped_text)
    escaped_text = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", escaped_text)
    return escaped_text


def render_generated_output(output: str, model_name: str, theme: str, run_id: int) -> None:
    tokens = THEME_TOKENS[theme]
    rendered_output = markdown_to_html(output)
    escaped_model = html.escape(model_name)
    clipboard_text = json.dumps(output)
    download_href = f"data:text/markdown;charset=utf-8,{quote(output)}"

    components.html(
        f"""
        <!doctype html>
        <html>
          <head>
            <style>
              :root {{
                --cc-panel: {tokens["panel"]};
                --cc-panel-alt: {tokens["panel_alt"]};
                --cc-text: {tokens["text"]};
                --cc-muted: {tokens["muted"]};
                --cc-border: {tokens["border"]};
                --cc-accent: {tokens["accent"]};
                --cc-accent-hover: {tokens["accent_hover"]};
                --cc-accent-soft: {tokens["accent_soft"]};
                --cc-accent-text: {tokens["accent_text"]};
                --cc-output: {tokens["output"]};
                --cc-shadow: {tokens["shadow"]};
              }}

              * {{
                box-sizing: border-box;
              }}

              body {{
                margin: 0;
                color: var(--cc-text);
                font-family: "Source Sans Pro", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              }}

              .output-pane {{
                background: var(--cc-panel);
                border: 1px solid var(--cc-border);
                border-radius: 8px;
                box-shadow: var(--cc-shadow);
                padding: 1.15rem;
              }}

              .output-header {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 1rem;
              }}

              .output-title {{
                min-width: 0;
              }}

              .output-title-row {{
                display: flex;
                align-items: center;
                gap: 0.55rem;
              }}

              h2 {{
                margin: 0;
                color: var(--cc-text);
                font-size: 1.25rem;
                line-height: 1.25;
              }}

              .status-text {{
                margin: 0.2rem 0 0;
                color: var(--cc-muted);
                font-size: 0.92rem;
              }}

              .output-actions {{
                display: flex;
                align-items: center;
                gap: 0.4rem;
              }}

              .icon-button {{
                display: inline-flex;
                width: 2.15rem;
                height: 2.15rem;
                align-items: center;
                justify-content: center;
                border: 1px solid var(--cc-border);
                border-radius: 6px;
                background: var(--cc-panel);
                color: var(--cc-text);
                cursor: pointer;
                text-decoration: none;
              }}

              .icon-button:hover {{
                border-color: var(--cc-accent);
                background: var(--cc-panel-alt);
              }}

              .icon-button svg {{
                width: 1.05rem;
                height: 1.05rem;
                stroke: currentColor;
                stroke-width: 2;
                stroke-linecap: round;
                stroke-linejoin: round;
                fill: none;
              }}

              .copy-status {{
                min-width: 3.25rem;
                color: var(--cc-muted);
                font-size: 0.82rem;
                font-weight: 700;
              }}

              .output-body {{
                min-height: 482px;
                max-height: 620px;
                overflow: auto;
                border: 1px solid var(--cc-border);
                border-radius: 6px;
                background: var(--cc-output);
                padding: 1.15rem;
                color: var(--cc-text);
                font-size: 1rem;
                line-height: 1.6;
              }}

              .output-body > :first-child {{
                margin-top: 0;
              }}

              .output-body > :last-child {{
                margin-bottom: 0;
              }}

              .output-body h1,
              .output-body h2,
              .output-body h3,
              .output-body h4,
              .output-body h5,
              .output-body h6 {{
                margin: 1rem 0 0.45rem;
                color: var(--cc-text);
                line-height: 1.25;
              }}

              .output-body h1 {{
                font-size: 1.45rem;
              }}

              .output-body h2 {{
                font-size: 1.28rem;
              }}

              .output-body h3 {{
                font-size: 1.12rem;
              }}

              .output-body p {{
                margin: 0 0 0.85rem;
              }}

              .output-body ul,
              .output-body ol {{
                margin: 0 0 0.9rem 1.25rem;
                padding: 0;
              }}

              .output-body li {{
                margin: 0.22rem 0;
              }}

              .output-body blockquote {{
                margin: 0 0 0.9rem;
                padding: 0.05rem 0 0.05rem 0.9rem;
                border-left: 3px solid var(--cc-accent);
                color: var(--cc-muted);
              }}

              .output-body .table-wrap {{
                margin: 0 0 0.95rem;
                overflow-x: auto;
                border: 1px solid var(--cc-border);
                border-radius: 6px;
              }}

              .output-body table {{
                width: 100%;
                border-collapse: collapse;
                background: var(--cc-output);
                font-size: 0.95rem;
              }}

              .output-body th,
              .output-body td {{
                border-bottom: 1px solid var(--cc-border);
                padding: 0.62rem 0.75rem;
                vertical-align: top;
              }}

              .output-body th {{
                background: var(--cc-panel-alt);
                color: var(--cc-text);
                font-weight: 800;
              }}

              .output-body tr:last-child td {{
                border-bottom: 0;
              }}

              .output-body a {{
                color: var(--cc-accent);
                font-weight: 700;
                text-decoration: none;
              }}

              .output-body a:hover {{
                color: var(--cc-accent-hover);
                text-decoration: underline;
              }}

              .output-body code {{
                border: 1px solid var(--cc-border);
                border-radius: 4px;
                background: var(--cc-panel-alt);
                padding: 0.08rem 0.26rem;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
                font-size: 0.92em;
              }}

              .output-body pre {{
                margin: 0 0 0.9rem;
                overflow: auto;
                border: 1px solid var(--cc-border);
                border-radius: 6px;
                background: var(--cc-panel-alt);
                padding: 0.85rem;
              }}

              .output-body pre code {{
                display: block;
                border: 0;
                background: transparent;
                padding: 0;
                white-space: pre;
              }}

              @media (max-width: 720px) {{
                .output-header {{
                  flex-direction: column;
                }}

                .output-actions {{
                  align-self: flex-start;
                }}
              }}
            </style>
          </head>
          <body>
            <div class="output-pane" data-run-id="{run_id}">
              <div class="output-header">
                <div class="output-title">
                  <div class="output-title-row">
                    <h2>Final Output</h2>
                    <div class="output-actions" aria-label="Output actions">
                      <button class="icon-button" type="button" title="Copy output" aria-label="Copy output" onclick="copyOutput()">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                      </button>
                      <a class="icon-button" title="Download output" aria-label="Download output" href="{download_href}" download="content-crew-output.md">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                          <path d="M7 10l5 5 5-5"></path>
                          <path d="M12 15V3"></path>
                        </svg>
                      </a>
                    </div>
                  </div>
                  <p class="status-text">Generated with {escaped_model}</p>
                </div>
                <div class="copy-status" id="copy-status" aria-live="polite"></div>
              </div>
              <div class="output-body">{rendered_output}</div>
            </div>
            <script>
              const outputText = {clipboard_text};

              function setCopyStatus(message) {{
                const status = document.getElementById("copy-status");
                status.textContent = message;
                window.clearTimeout(window.copyStatusTimer);
                window.copyStatusTimer = window.setTimeout(() => {{
                  status.textContent = "";
                }}, 1500);
              }}

              async function copyOutput() {{
                try {{
                  if (navigator.clipboard && window.isSecureContext) {{
                    await navigator.clipboard.writeText(outputText);
                  }} else {{
                    const textArea = document.createElement("textarea");
                    textArea.value = outputText;
                    textArea.style.position = "fixed";
                    textArea.style.left = "-9999px";
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    document.execCommand("copy");
                    textArea.remove();
                  }}
                  setCopyStatus("Copied");
                }} catch (error) {{
                  setCopyStatus("Copy failed");
                }}
              }}
            </script>
          </body>
        </html>
        """,
        height=720,
        scrolling=False,
    )


if __name__ == "__main__":
    main()
