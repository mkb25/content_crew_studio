from __future__ import annotations

import html
import json
from urllib.parse import quote

from pydantic import ValidationError
import streamlit as st
import streamlit.components.v1 as components

from app.crew_workflow import generate_with_content_crew
from app.errors import AppError
from app.prompts import LENGTH_GUIDANCE
from app.schemas import GenerateRequest

LENGTH_OPTIONS = {
    "Short": "short",
    "Medium": "medium",
    "Long": "long",
}

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

    if "theme" not in st.session_state:
        st.session_state["theme"] = "Light"

    theme = st.session_state["theme"]

    inject_theme_css(theme)
    header_column, theme_column = st.columns([3.2, 1], gap="large")
    with header_column:
        render_header()
    with theme_column:
        st.markdown('<div class="theme-label">Appearance</div>', unsafe_allow_html=True)
        next_theme = "Dark" if theme == "Light" else "Light"
        if st.button(f"{next_theme} mode", key="theme_toggle"):
            st.session_state["theme"] = next_theme
            st.rerun()

    input_column, output_column = st.columns([0.95, 1.55], gap="large")

    with input_column:
        st.markdown(
            """
            <div class="section-heading">
              <span>Compose</span>
              <small>Brief the crew</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
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
            submitted = st.form_submit_button("Run agents", type="primary")

    with output_column:
        render_output()

    if submitted:
        request = build_request(
            topic=topic,
            style=style,
            audience=audience,
            length=LENGTH_OPTIONS[length_label],
        )
        if request is not None:
            run_generation(request)
            st.rerun()


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
    value = LENGTH_OPTIONS[label]
    return f"{label}"


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
            st.error(exc.detail)
            return
        except Exception as exc:  # pragma: no cover - depends on provider/network behavior
            st.error(f"Agent workflow failed: {exc}")
            return

    st.session_state["generated_output"] = output
    st.session_state["generated_model"] = model_name


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
    )


def render_generated_output(output: str, model_name: str, theme: str) -> None:
    tokens = THEME_TOKENS[theme]
    escaped_output = html.escape(output)
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
                white-space: pre-wrap;
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
            <div class="output-pane">
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
              <div class="output-body">{escaped_output}</div>
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
