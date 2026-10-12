import logging

from telegram.ext import Application

from finance_bot.agent import Agent
from finance_bot.config import Settings
from finance_bot.core import Assistant
from finance_bot.db import Database
from finance_bot.llm import FoundryLLM
from finance_bot.telegram_bot import build_application


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
    )
    # httpx logs every request URL at INFO, and Telegram URLs contain the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = Settings()
    api_key = settings.azure_openai_api_key
    db = Database(settings.database_path)
    llm = FoundryLLM(
        settings.azure_openai_endpoint,
        settings.azure_openai_deployment,
        api_key.get_secret_value() if api_key else None,
    )
    assistant = Assistant(db, Agent(db, llm), settings.invite_code_list)

    async def shutdown(_: Application) -> None:
        await llm.close()
        db.close()

    token = settings.telegram_bot_token.get_secret_value()
    build_application(token, assistant, shutdown).run_polling()


if __name__ == "__main__":
    main()
