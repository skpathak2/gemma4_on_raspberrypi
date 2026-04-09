from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .config import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT


@dataclass
class ChatConfig:
    model: str = DEFAULT_MODEL
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    temperature: float = 0.7
    max_tokens: int = 512  # 0 = model default
    mode: str = "default"


@dataclass
class ChatState:
    config: ChatConfig = field(default_factory=ChatConfig)
    # Ollama-style chat history
    history: List[Dict[str, str]] = field(default_factory=list)


# In-memory per-chat state
_chat_states: Dict[int, ChatState] = {}


def get_state(chat_id: int) -> ChatState:
    if chat_id not in _chat_states:
        _chat_states[chat_id] = ChatState()
    return _chat_states[chat_id]
