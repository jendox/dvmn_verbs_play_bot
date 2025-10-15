import logging

import anyio
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from dialogflow import DetectIntentHandler

__all__ = (
    "TelegramBot",
    "TG_LOGGER_NAME",
)

TG_LOGGER_NAME = "tg"


class TelegramBot:
    def __init__(
        self,
        api_bot: telegram.Bot,
        detect_intent: DetectIntentHandler,
    ) -> None:
        self._api_bot = api_bot
        self._detect_intent = detect_intent
        self.logger = logging.getLogger(TG_LOGGER_NAME)

    async def start(self, update: Update, context) -> None:
        await update.message.reply_text(text="Здравствуйте!")

    async def reply(self, update: Update, context) -> None:
        text, is_fallback = await self._detect_intent(
            update.effective_user.id,
            update.effective_message.text,
        )
        await update.message.reply_text(text)

    async def run(self):
        application = Application.builder().bot(self._api_bot).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.reply))
        try:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            await anyio.sleep_forever()
        except Exception as e:
            self.logger.error(e, exc_info=True)
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
