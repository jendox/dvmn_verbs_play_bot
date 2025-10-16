import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import dialogflow
from logs import setup_logging

TG_LOGGER_NAME = "tg"

logger = logging.getLogger(TG_LOGGER_NAME)


async def start(update: Update, context) -> None:
    await update.message.reply_text(text="Здравствуйте!")


def make_reply_handler(project_id: str):
    async def reply(update: Update, context) -> None:
        session_id = f"tg-{update.effective_user.id}"
        try:
            text, is_fallback = dialogflow.detect_intent(
                project_id,
                session_id,
                update.effective_message.text,
            )
            await update.message.reply_text(text)
        except Exception as error:
            logger.error(f"Ошибка отправки ответа пользователю: {error}")

    return MessageHandler(filters.TEXT & ~filters.COMMAND, reply)


def main():
    load_dotenv()
    try:
        bot_token = os.environ["TELEGRAM_TOKEN"]
        chat_id = os.environ["TELEGRAM_CHAT_ID"]
        project_id = os.environ["DIALOGFLOW_PROJECT_ID"]

        setup_logging(bot_token, chat_id, TG_LOGGER_NAME)
        application = Application.builder().token(bot_token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(make_reply_handler(project_id))
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyError as e:
        logger.error(f"Не настроены необходимые переменные окружения: {e}")
    except Exception as exc:
        logger.error(f"Неожиданное исключение: {exc}")
    except KeyboardInterrupt:
        logger.info("Завершено пользователем")


if __name__ == "__main__":
    main()
