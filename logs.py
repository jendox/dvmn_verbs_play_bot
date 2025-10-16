import html
import logging
import traceback
from textwrap import dedent

import httpx

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
            "\n\n<b>Трассировка</b>\n"
            f"<pre>{tb_html}</pre>"
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


class TelegramSyncHTTPHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__()
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._chat_id = chat_id

    def emit(self, record: logging.LogRecord) -> None:
        text = _format_logger_message_html(record)
        message_data = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            httpx.post(self._url, data=message_data, timeout=5.0)
        except Exception:
            super().handleError(record)


def setup_logging(bot_token: str, chat_id: str, logger_name: str) -> None:
    log_handler = TelegramSyncHTTPHandler(bot_token, chat_id)
    log_handler.setLevel(logging.WARNING)
    log_handler.setFormatter(logging.Formatter(LOGGER_FORMAT))
    logging.getLogger(logger_name).addHandler(log_handler)
    logging.getLogger(DF_LOGGER_NAME).addHandler(log_handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
