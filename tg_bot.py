import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import dialog_flow


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text="Здравствуйте")


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await dialog_flow.get_response(
        dialog_flow.dialogflow_project_id.get(),
        update.effective_user.id,
        update.effective_message.text,
    )
    await update.message.reply_text(text)


def start_bot():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
