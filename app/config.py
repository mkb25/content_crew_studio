from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Fix Windows console encoding ────────────────────────────
# CrewAI logs emoji characters (🚀, 📋, etc.) that crash on
# Windows terminals using the default cp1252 codec.
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DIR = BASE_DIR / ".local"

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
PLACEHOLDER_GROQ_KEYS = {"", "your_groq_api_key_here", "your_groq_api_key"}


def configure_local_paths() -> None:
    os.environ.setdefault("XDG_DATA_HOME", str(LOCAL_DIR / "share"))
    os.environ.setdefault("XDG_CONFIG_HOME", str(LOCAL_DIR / "config"))
    os.environ.setdefault("XDG_CACHE_HOME", str(LOCAL_DIR / "cache"))


configure_local_paths()
load_dotenv(BASE_DIR / ".env")


# ── Strip crewai cache_breakpoint for non-Anthropic providers ──
# crewai 1.15.5 injects {"cache_breakpoint": True} into every message
# for prompt-caching purposes. This field is only valid for Anthropic.
# Groq (and other OpenAI-compatible providers) reject it with a 400
# "property 'cache_breakpoint' is unsupported" error.
# We patch litellm.completion to strip it before every API call.
def _patch_litellm_strip_cache_breakpoint() -> None:
    try:
        import litellm

        _original_completion = litellm.completion

        def _patched_completion(*args: object, **kwargs: object) -> object:
            messages = kwargs.get("messages")
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict):
                        msg.pop("cache_breakpoint", None)
            return _original_completion(*args, **kwargs)

        litellm.completion = _patched_completion  # type: ignore[assignment]
    except Exception:
        pass  # If litellm isn't installed yet, the crew_workflow will report it.


_patch_litellm_strip_cache_breakpoint()

