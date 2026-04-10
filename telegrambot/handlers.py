# Text messages, photos, and unknown commands.

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .state import get_state
from .markdown_utils import reply_markdown
from .llm import build_ollama_messages, call_ollama_chat
from .vision import analyze_image_with_ollama
from .config import DOWNLOAD_DIR
from . import commands as cmd


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    user_text = update.message.text

    messages = build_ollama_messages(state, user_text)

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

    state.history.append({"role": "user", "content": user_text})
    state.history.append({"role": "assistant", "content": answer})

    await reply_markdown(update, context, answer)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos and send them to a vision model, then delete the file."""
    if not update.message or not update.message.photo:
        return

    chat_id = update.effective_chat.id
    state = get_state(chat_id)

    # highest-resolution version
    photo_size = update.message.photo[-1]
    file = await photo_size.get_file()

    img_dir = DOWNLOAD_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    file_path = img_dir / f"{file.file_id}.jpg"

    caption = (update.message.caption or "").strip()
    question = caption or "Describe this image."

    try:
        # 1) download
        await file.download_to_drive(str(file_path))

        # 2) send to vision model
        answer = await asyncio.to_thread(
            analyze_image_with_ollama,
            str(file_path),
            question,
            state,
        )

        # 3) update history
        state.history.append({"role": "user", "content": f"[Image] {question}"})
        state.history.append({"role": "assistant", "content": answer})

        await reply_markdown(update, context, answer)

    except Exception as e:
        logging.exception("Error processing image")
        await reply_markdown(update, context, f"Error analyzing image: `{e}`")

    finally:
        # 4) best-effort delete of the downloaded image
        try:
            file_path.unlink(missing_ok=True)
        except Exception as e:
            logging.warning(f"Could not delete temp image {file_path}: {e}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cmd_text = ""
    if update.message and update.message.text:
        cmd_text = update.message.text.split()[0]
    text = (
        f"I don't recognize the command `{cmd_text}`.\n"
        "Use /help to see all available commands."
    )
    await reply_markdown(update, context, text)


def register_handlers(application: Application) -> None:
    """Register all command & message handlers on the Application."""

    # commands
    application.add_handler(CommandHandler("start", cmd.start))
    application.add_handler(CommandHandler("help", cmd.help_command))

    application.add_handler(CommandHandler("see_models", cmd.see_models))
    application.add_handler(CommandHandler("current_model", cmd.current_model))
    application.add_handler(CommandHandler("change_model", cmd.change_model))

    application.add_handler(CommandHandler("reset", cmd.reset))
    application.add_handler(CommandHandler("set_system", cmd.set_system))
    application.add_handler(CommandHandler("see_system", cmd.see_system))
    application.add_handler(CommandHandler("mode", cmd.mode_command))

    application.add_handler(CommandHandler("set_temperature", cmd.set_temperature))
    application.add_handler(CommandHandler("see_temperature", cmd.see_temperature))
    application.add_handler(CommandHandler("set_max_tokens", cmd.set_max_tokens))
    application.add_handler(CommandHandler("see_max_tokens", cmd.see_max_tokens))

    application.add_handler(CommandHandler("context", cmd.context_cmd))
    application.add_handler(CommandHandler("ping", cmd.ping))

    application.add_handler(CommandHandler("summarize", cmd.summarize_text))
    application.add_handler(CommandHandler("summarize_before", cmd.summarize_before))
    application.add_handler(CommandHandler("translate", cmd.translate_cmd))
    application.add_handler(CommandHandler("web", cmd.web_cmd))

    # photos → vision model
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # normal text chat
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )

    # unknown commands (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
