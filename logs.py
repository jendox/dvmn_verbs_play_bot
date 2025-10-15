import html
import logging
import queue
from collections.abc import Callable, Coroutine
from textwrap import dedent
from typing import Any

import anyio
import telegram
from telegram.constants import ParseMode

from bots.tg import TG_LOGGER_NAME
from bots.vk import VK_LOGGER_NAME
from dialogflow import DF_LOGGER_NAME

__all__ = ("setup_logging",)

LOGGER_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOGS_QUEUE_MAX_SIZE = 200
QUEUE_SLEEP_TIME = 1.5


def format_logger_message_html(record: logging.LogRecord) -> str:
    level_icon = {
        "CRITICAL": "🚨",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "INFO": "ℹ️",
        "DEBUG": "🐞",
    }.get(record.levelname, "❗")

    message = html.escape(record.getMessage())
    logger_name = html.escape(record.name)
    exc_info = ""

    if record.exc_info:
        import traceback
        tb = "".join(traceback.format_exception(*record.exc_info))
        exc_info = f"\n\n<pre>{html.escape(tb[-1500:])}</pre>"

    return dedent(
        f"""\
        {level_icon} <b>Логгер</b>

        <b>Уровень:</b> {record.levelname}
        <b>Источник:</b> {logger_name}

        <b>Сообщение:</b> {message}{exc_info}
        """,
    )


class LogsHandler(logging.Handler):
    def __init__(self, logs_queue: queue.Queue[logging.LogRecord]):
        super().__init__()
        self._queue = logs_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            pass


class TelegramLogger:
    def __init__(self, bot: telegram.Bot, chat_id: int) -> None:
        self._bot = bot
        self._chat_id = chat_id
        self._queue = queue.Queue[logging.LogRecord](LOGS_QUEUE_MAX_SIZE)

    @property
    def logs_queue(self) -> queue.Queue[logging.LogRecord]:
        return self._queue

    async def _send_html_message(self, message: str) -> None:
        await self._bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    async def logs_polling(self) -> None:
        while True:
            try:
                record = self._queue.get(block=False)
                message = format_logger_message_html(record)
                await self._send_html_message(message)
            except queue.Empty:
                await anyio.sleep(QUEUE_SLEEP_TIME)


def setup_logging(bot: telegram.Bot, chat_id: int) -> Callable[[], Coroutine[Any, Any, None]]:
    logger = TelegramLogger(bot, chat_id)
    log_handler = LogsHandler(logger.logs_queue)
    log_handler.setLevel(logging.WARNING)
    log_handler.setFormatter(logging.Formatter(LOGGER_FORMAT))
    logging.getLogger(VK_LOGGER_NAME).addHandler(log_handler)
    logging.getLogger(TG_LOGGER_NAME).addHandler(log_handler)
    logging.getLogger(DF_LOGGER_NAME).addHandler(log_handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger.logs_polling
