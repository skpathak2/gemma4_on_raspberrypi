from __future__ import annotations
import os
from pathlib import Path
from time import gmtime, strftime

# Telegram & Ollama configuration
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "PUT_YOUR_TOKEN_HERE") #<--- Change here your telegram bot token
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") #<--- Make sure ollama is running here

# Default Model. For vision, the model must be vision-capable, e.g. llava
DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "gemma3:12b")  #<--- Change here your default model
VISION_MODEL = DEFAULT_MODEL

DEFAULT_SYSTEM_PROMPT: str = "You are a helpful, concise assistant. Use Markdown."

now = strftime("%Y-%m-%d", gmtime())
NOW_PROMPT = f" Date: {now}."
DEFAULT_SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT + NOW_PROMPT

# Predefined behaviour modes (system prompts)
MODES = {
    "default": DEFAULT_SYSTEM_PROMPT,
    "coder": (
        "You are a precise, concise programming assistant. "
        "Prefer examples and explain edge cases briefly. "
        "Respond in Markdown with fenced code blocks when useful."
    ),
    "translator": (
        "You are a translation assistant. Translate text and briefly explain "
        "tricky phrases when helpful. Respond in Markdown."
    ),
    "teacher": (
        "You are a patient teacher. Explain concepts step-by-step with "
        "short paragraphs. Respond in Markdown."
    ),
}

# Where Telegram images are downloaded to
DOWNLOAD_DIR: Path = Path(os.getenv("PERSONALBOT_DOWNLOAD_DIR", "downloads"))
