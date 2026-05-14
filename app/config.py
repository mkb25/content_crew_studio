from __future__ import annotations

import os
from pathlib import Path

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
