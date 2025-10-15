# ruff: noqa: F401, I001
from config import (
    AppSettings,
    env,
)

import logging

import anyio
import telegram

from bots.tg import TelegramBot
from bots.vk import VKBot
from logs import setup_logging


async def main():
    from dialogflow import DialogFlow

    settings = AppSettings.load()

    async with DialogFlow(settings.dialogflow.project_id) as df:
        api_bot = telegram.Bot(settings.telegram.bot_token)
        tg_bot = TelegramBot(api_bot, df.detect_intent)
        vk_bot = VKBot(settings.vk.api_token, settings.vk.group_id, df.detect_intent)
        logs_handler = setup_logging(api_bot, settings.telegram.chat_id)

        async with anyio.create_task_group() as task_group:
            task_group.start_soon(logs_handler)
            task_group.start_soon(tg_bot.run)
            task_group.start_soon(vk_bot.run)


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        logging.info("Завершение работы")
