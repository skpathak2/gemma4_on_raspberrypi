# All commandas such as /help, /web, /summarize, etc. live here

from __future__ import annotations

import asyncio
from typing import List
from time import gmtime, strftime

from telegram import Update
from telegram.ext import ContextTypes

from web.web_tools import web_search, summarise_sources

from .config import MODES
from .state import get_state
from .markdown_utils import reply_markdown
from .llm import call_ollama_chat, build_ollama_messages, list_ollama_models


def get_help_markdown() -> str:
    return (
        "**Commands**\n"
        "/help - List all commands\n"
        "/see_models - Show all available Ollama models\n"
        "/current_model - Show the current model\n"
        "/change_model `<name>` - Switch to a different model\n"
        "/reset - Clear the chat history\n"
        "/set_system `<text>` - Set the system prompt\n"
        "/see_system - Show the current system prompt\n"
        "/mode `<name>` - Change behavior (pre-defined system prompts)\n"
        "/set_temperature `<float>` - Set creativity level\n"
        "/see_temperature - See the creativity level\n"
        "/set_max_tokens `<int>` - Set max new tokens (0 = model default)\n"
        "/see_max_tokens - See current max_tokens\n"
        "/context - Show current chat configuration\n"
        "/ping - Test responsiveness\n"
        "/summarize `<text>` - Summarize the given text\n"
        "/summarize_before - Summarize the conversation so far\n"
        "/translate `<lang>` `<text>` - Translate text with the model\n"
        "/web `<query>` - Search the web and answer using DDGS results\n"
    )


# --- basic ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """First message: same as /help."""
    get_state(update.effective_chat.id)
    await reply_markdown(update, context, get_help_markdown())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_markdown(update, context, get_help_markdown())


async def see_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        models = await asyncio.to_thread(list_ollama_models)
    except Exception as e:
        await reply_markdown(update, context, f"Error listing models: `{e}`")
        return

    if not models:
        await reply_markdown(update, context, "No models found on this Ollama server.")
        return

    body = "\n".join(f"- `{m}`" for m in models)
    await reply_markdown(update, context, f"**Available models:**\n{body}")


async def current_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    await reply_markdown(update, context, f"Current model: `{state.config.model}`")


async def change_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    if not context.args:
        await reply_markdown(
            update,
            context,
            "Usage: `/change_model model_name` (see `/see_models`)",
        )
        return
    new_model = " ".join(context.args).strip()
    state.config.model = new_model
    await reply_markdown(update, context, f"Model changed to `{new_model}`.")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    state.history.clear()
    await reply_markdown(update, context, "Chat history cleared.")


async def set_system(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    if not context.args:
        await reply_markdown(update, context, "Usage: `/set_system you are ...`")
        return
    state.config.system_prompt = " ".join(context.args)
    state.config.mode = "custom"
    await reply_markdown(update, context, "System prompt updated.")


async def see_system(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    if not state.config.system_prompt:
        await reply_markdown(update, context, "No system prompt set.")
        return
    await reply_markdown(
        update,
        context,
        f"**Current system prompt** (mode: `{state.config.mode}`):\n\n"
        f"{state.config.system_prompt}",
    )


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    if not context.args:
        modes_list = "\n".join(f"- `{name}`" for name in MODES.keys())
        await reply_markdown(
            update,
            context,
            "**Available modes:**\n"
            f"{modes_list}\n\n"
            "Usage: `/mode coder`",
        )
        return

    m = context.args[0].lower()
    if m not in MODES:
        modes_list = ", ".join(f"`{name}`" for name in MODES.keys())
        await reply_markdown(
            update,
            context,
            f"Unknown mode `{m}`.\nAvailable modes: {modes_list}",
        )
        return

    state.config.mode = m
    state.config.system_prompt = MODES[m]
    await reply_markdown(
        update,
        context,
        f"Mode set to `{m}` and system prompt updated.",
    )


async def set_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    if not context.args:
        await reply_markdown(update, context, "Usage: `/set_temperature 0.2`")
        return
    try:
        value = float(context.args[0])
    except ValueError:
        await reply_markdown(update, context, "Temperature must be a number, e.g. `0.7`.")
        return
    if not (0.0 <= value <= 2.0):
        await reply_markdown(
            update,
            context,
            "Temperature should be between `0.0` and `2.0`.",
        )
        return
    state.config.temperature = value
    await reply_markdown(update, context, f"Temperature set to `{value}`.")


async def see_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    await reply_markdown(update, context, f"Current temperature: `{state.config.temperature}`")


async def set_max_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    if not context.args:
        await reply_markdown(
            update,
            context,
            "Usage: `/set_max_tokens 512` (0 = model default)",
        )
        return
    try:
        value = int(context.args[0])
    except ValueError:
        await reply_markdown(update, context, "max_tokens must be an integer.")
        return
    if value < 0:
        await reply_markdown(update, context, "max_tokens must be >= 0.")
        return
    state.config.max_tokens = value
    await reply_markdown(
        update,
        context,
        f"max_tokens set to `{value}` (0 means model default).",
    )


async def see_max_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    await reply_markdown(
        update,
        context,
        f"Current max_tokens: `{state.config.max_tokens}`",
    )


async def context_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    cfg = state.config
    sys_preview = (
        cfg.system_prompt[:200] + "…"
        if len(cfg.system_prompt) > 200
        else cfg.system_prompt
    )
    text = (
        "**Current chat configuration**\n"
        f"- Model: `{cfg.model}`\n"
        f"- Mode: `{cfg.mode}`\n"
        f"- Temperature: `{cfg.temperature}`\n"
        f"- max_tokens: `{cfg.max_tokens}`\n"
        f"- System prompt (preview):\n"
        f"```\n{sys_preview}\n```"
    )
    await reply_markdown(update, context, text)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(update.effective_chat.id)
    await reply_markdown(update, context, f"Pong! (model: `{state.config.model}`)")

# --------- Summarization ---------

async def summarize_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /summarize <text>  → summarize arbitrary text (does NOT touch history)
    """
    state = get_state(update.effective_chat.id)

    if not context.args:
        await reply_markdown(
            update,
            context,
            "Usage: `/summarize your long text here...`",
        )
        return

    input_text = " ".join(context.args)
    messages = [
        {
            "role": "system",
            "content": "Summarize the user's text in a few clear bullet points.",
        },
        {
            "role": "user",
            "content": input_text,
        },
    ]

    try:
        answer = await call_ollama_chat(
            messages,
            state.config.model,
            state.config.temperature,
            state.config.max_tokens,
        )
    except Exception as e:
        answer = f"Error summarizing: `{e}`"

    await reply_markdown(update, context, answer)


async def summarize_before(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /summarize_before  → summarize recent conversation history.
    """
    state = get_state(update.effective_chat.id)
    if not state.history:
        await reply_markdown(update, context, "Nothing to summarize yet.")
        return

    recent = state.history[-10:]
    transcript_lines = []
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        transcript_lines.append(f"{role}: {content}")
    transcript = "\n".join(transcript_lines)

    prompt = (
        "Summarize the following conversation in a few bullet points. "
        "Focus on the main questions, answers, and decisions.\n\n"
        f"{transcript}"
    )
    messages = [
        {"role": "system", "content": "You are a summarization assistant."},
        {"role": "user", "content": prompt},
    ]

    try:
        answer = await call_ollama_chat(
            messages,
            state.config.model,
            state.config.temperature,
            state.config.max_tokens,
        )
    except Exception as e:
        answer = f"Error summarizing: `{e}`"

    await reply_markdown(update, context, answer)


# --------- Translation ---------

async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /translate <lang> <text>
    """
    state = get_state(update.effective_chat.id)
    if len(context.args) < 2:
        await reply_markdown(
            update,
            context,
            "Usage: `/translate spanish This is my text...`",
        )
        return

    target_lang = context.args[0]
    text_to_translate = " ".join(context.args[1:])

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a translation assistant. Translate the user's text "
                f"into {target_lang}. Return only the translation, no commentary."
            ),
        },
        {"role": "user", "content": text_to_translate},
    ]

    try:
        answer = await call_ollama_chat(
            messages,
            state.config.model,
            state.config.temperature,
            state.config.max_tokens,
        )
    except Exception as e:
        answer = f"Error translating: `{e}`"

    await reply_markdown(update, context, answer)


# --------- Web search via your ddgs wrapper ---------

async def web_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /web <query>

    1) Run DDGS via core/web_tools.web_search
    2) Feed query + web results to the LLM
    3) Return the LLM's synthesized answer (optionally with a short sources list)
    """
    state = get_state(update.effective_chat.id)

    if not context.args:
        await reply_markdown(update, context, "Usage: `/web your search query...`")
        return

    query = " ".join(context.args)

    try:
        # 1) Get web results from your DDGS wrapper
        sources = await asyncio.to_thread(web_search, query, 5)
    except Exception as e:
        await reply_markdown(update, context, f"Error during web search: `{e}`")
        return

    if not sources:
        # No results – just ask the model normally
        messages = build_ollama_messages(
            state,
            f"(No web results were found.) Answer the following question as best you can:\n\n{query}",
        )
    else:
        # 2) Summarize sources into markdown for the model
        sources_md = summarise_sources(sources, max_chars=4000)

        # Build a special prompt for web-augmented answering
        now = strftime("%Y-%m-%d", gmtime())
        web_prompt = (
            "You are a web-augmented assistant.\n"
            f" Today is: {now} (YYYY-MM-DD)\n"
            "You are given a user question and some web search results.\n"
            "- Use ONLY the information in the web results when possible.\n"
            "- If something is not supported by the results, say you are not sure.\n"
            "- When helpful, mention which URL supports a key fact.\n\n"
            f"User question:\n{query}\n\n"
            f"Web search results:\n{sources_md}\n"
        )

        # Do NOT add this to normal history (keeps main chat clean)
        messages = [
            {"role": "system", "content": state.config.system_prompt},
            {"role": "user", "content": web_prompt},
        ]

    try:
        answer = await call_ollama_chat(
            messages,
            state.config.model,
            state.config.temperature,
            state.config.max_tokens,
        )
    except Exception as e:
        await reply_markdown(update, context, f"Error talking to Ollama: `{e}`")
        return

    # Optionally: show a tiny sources list under the answer
    if sources:
        top_urls = [s.get("url") for s in sources[:3] if s.get("url")]
        if top_urls:
            answer += "\n\n**Sources (top):**\n" + "\n".join(f"- {u}" for u in top_urls)

    await reply_markdown(update, context, answer)