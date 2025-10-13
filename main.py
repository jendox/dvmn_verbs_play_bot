import logging
import os
from contextvars import ContextVar

from dotenv import load_dotenv
from google.cloud import dialogflow
from google.cloud.dialogflow_v2 import DetectIntentRequest
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

dialogflow_project_id: ContextVar[str] = ContextVar("DialogFlow Project ID")

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text="Здравствуйте")


async def response_to_customer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await get_dialogflow_response(
        dialogflow_project_id.get(),
        update.effective_user.id,
        update.effective_message.text,
    )
    await update.message.reply_text(text)


async def get_dialogflow_response(
    project_id: str,
    session_id: int,
    text: str,
    language_code: str = "ru",
):
    async with dialogflow.SessionsAsyncClient() as session_client:
        session = session_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = await session_client.detect_intent(
            DetectIntentRequest(
                session=session,
                query_input=query_input,
            ),
        )
        return response.query_result.fulfillment_text


def main():
    dialogflow_project_id.set(os.getenv("PROJECT_ID"))
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, response_to_customer))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
