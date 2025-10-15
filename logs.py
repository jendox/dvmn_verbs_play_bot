import html
import logging
import queue
import traceback
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

TG_HARD_LIMIT = 4096
BODY_BUDGET = 2800


def _truncate_middle(text: str, max_len: int, ellipsis_: str = " … ") -> str:
    if len(text) <= max_len:
        return text
    keep = max_len - len(ellipsis_)
    head = keep // 2
    tail = keep - head
    return text[:head] + ellipsis_ + text[-tail:]


def _format_logger_message_html(record: logging.LogRecord) -> str:
    level_icon = {
        "CRITICAL": "🚨", "ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️", "DEBUG": "🐞",
    }.get(record.levelname, "❗")

    message = html.escape(record.getMessage())
    logger_name = html.escape(record.name)

    exc_block = ""
    if record.exc_info:
        parts = traceback.format_exception(*record.exc_info)
        tb_text = "".join(parts)
        tb_text = _truncate_middle(tb_text, BODY_BUDGET)
        tb_html = html.escape(tb_text)

        exc_block = (
            "\n\n<b>Трассировка (tap, чтобы раскрыть)</b>\n"
            f"<tg-spoiler><pre>{tb_html}</pre></tg-spoiler>"
        )

    doc = dedent(f"""\
        {level_icon} <b>Логгер</b>

        <b>Уровень:</b> {record.levelname}
        <b>Источник:</b> {logger_name}

        <b>Сообщение:</b> {message}{exc_block}
    """)

    if len(doc) > TG_HARD_LIMIT:
        doc = doc[:TG_HARD_LIMIT - 1]
    return doc


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
                message = _format_logger_message_html(record)
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
