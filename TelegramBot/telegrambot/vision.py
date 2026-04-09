# image → vision model via Ollama
# Uses Ollama’s documented vision API: send a message with an images array that contains base64-encoded image data.

from __future__ import annotations

import base64
from typing import Any, Dict

import requests

from .config import OLLAMA_BASE_URL, VISION_MODEL
from .state import ChatState


def _encode_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _choose_vision_model(state: ChatState) -> str:
    """
    Prefer the chat's current model if it looks like a vision model,
    otherwise fall back to the configured VISION_MODEL.
    """
    model = state.config.model or ""
    lower = model.lower()
    if "vision" in lower or "llava" in lower:
        return model
    if VISION_MODEL:
        return VISION_MODEL
    return model or "llama3.2-vision"


def analyze_image_with_ollama(
    image_path: str,
    question: str,
    state: ChatState,
) -> str:
    """
    Send an image + question to an Ollama vision model via /api/chat and return the answer.
    """
    model = _choose_vision_model(state)
    img_b64 = _encode_image_base64(image_path)

    messages = [
        {
            "role": "user",
            "content": question,
            "images": [img_b64],
        }
    ]

    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": state.config.temperature},
    }
    if state.config.max_tokens > 0:
        payload["options"]["num_predict"] = state.config.max_tokens

    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]
