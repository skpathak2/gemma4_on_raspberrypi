from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from chatgpt_md_converter import telegram_format


def markdown_to_telegram_html(text: str) -> str:
    """Convert ChatGPT-style Markdown into Telegram-safe HTML."""
    return telegram_format(text)


async def reply_markdown(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> None:
    """Reply to the current message using Markdown rendered as Telegram HTML."""
    if not update.message:
        return
    html = markdown_to_telegram_html(text)
    await update.message.reply_text(html, parse_mode=ParseMode.HTML)
