import logging
from collections.abc import Awaitable, Callable
from typing import Self

from google.cloud import dialogflow
from google.cloud.dialogflow_v2 import DetectIntentRequest, Intent, SessionsAsyncClient

__all__ = (
    "DialogFlow",
    "DF_LOGGER_NAME",
    "DetectIntentHandler",
)

DF_LOGGER_NAME = "dialogflow"

DetectIntentHandler = Callable[[int, str], Awaitable[tuple[str, bool]]]


class DialogFlow:
    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self._session_client: SessionsAsyncClient | None = None
        self.logger = logging.getLogger(DF_LOGGER_NAME)

    async def __aenter__(self) -> Self:
        self._session_client = dialogflow.SessionsAsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session_client:
            transport = getattr(self._session_client, "transport", None)
            if transport:
                await transport.close()
        self._session_client = None

    async def detect_intent(
        self,
        session_id: int,
        text: str,
        language_code: str = "ru",
    ) -> tuple[str, bool]:
        session = self._session_client.session_path(self._project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        try:
            response = await self._session_client.detect_intent(
                DetectIntentRequest(
                    session=session,
                    query_input=query_input,
                ),
            )
            return response.query_result.fulfillment_text, response.query_result.intent.is_fallback
        except Exception as e:
            self.logger.error(e, exc_info=True)
            return "Неожиданная ошибка. Повторите попытку позже"

    def create_intent(
        self,
        display_name: str,
        training_phrases_parts: list[str],
        message_texts: list[str],
    ) -> Intent:
        intents_client = dialogflow.IntentsClient()

        parent = dialogflow.AgentsClient.agent_path(self._project_id)
        training_phrases = []
        for training_phrases_part in training_phrases_parts:
            part = dialogflow.Intent.TrainingPhrase.Part(text=training_phrases_part)
            training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
            training_phrases.append(training_phrase)

        text = dialogflow.Intent.Message.Text(text=message_texts)
        message = dialogflow.Intent.Message(text=text)

        intent = dialogflow.Intent(
            display_name=display_name, training_phrases=training_phrases, messages=[message],
        )

        return intents_client.create_intent(request={"parent": parent, "intent": intent})
