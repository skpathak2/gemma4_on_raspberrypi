# Text Ollama helper

from __future__ import annotations
from typing import Any, Dict, List
import httpx  # Swapped 'requests' for 'httpx'

from .config import OLLAMA_BASE_URL
from .state import ChatState

# Notice the 'async def' here
async def call_ollama_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    Call Ollama /api/chat with the given messages and return assistant content.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    print(url) 
    
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    
    if max_tokens > 0:
        payload["options"]["num_predict"] = max_tokens
        
    print("invoking ollamachat")
    
    # Use an async httpx client instead of synchronous requests
    async with httpx.AsyncClient(timeout=600.0) as client:
        resp = await client.post(url, json=payload)
        
    print(resp)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]


def build_ollama_messages(state: ChatState, user_text: str) -> List[Dict[str, str]]:
    """
    Build a message list containing system prompt, history and new user message.
    """
    messages: List[Dict[str, str]] = []
    if state.config.system_prompt:
        messages.append({"role": "system", "content": state.config.system_prompt})
    messages.append({"role": "user", "content": user_text})
    return messages


# This should likely be made async as well to prevent blocking on startup/commands
async def list_ollama_models() -> List[str]:
    """
    Call /api/tags on the Ollama server and return available model names.
    """
    url = f"{OLLAMA_BASE_URL}/api/tags"
    print("invoking modelnames")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        
    resp.raise_for_status()
    data = resp.json()
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]