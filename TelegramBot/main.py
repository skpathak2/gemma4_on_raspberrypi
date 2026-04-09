from __future__ import annotations

import logging
from telegram.ext import ApplicationBuilder

from telegrambot.config import BOT_TOKEN
from telegrambot.handlers import register_handlers


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    if not BOT_TOKEN or BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError(
            "Set TELEGRAM_BOT_TOKEN env var or edit BOT_TOKEN in personalbot/config.py."
        )

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(300.0)
        .read_timeout(300.0)
        .write_timeout(300.0)
        .pool_timeout(300.0)
        .build()
    )
    register_handlers(application)
    application.run_polling()


if __name__ == "__main__":
    main()
