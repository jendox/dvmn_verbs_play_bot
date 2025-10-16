import logging

from google.cloud import dialogflow
from google.cloud.dialogflow_v2 import DetectIntentRequest, Intent

DF_LOGGER_NAME = "dialogflow"

logger = logging.getLogger(DF_LOGGER_NAME)


def detect_intent(
    project_id: str,
    session_id: str,
    text: str,
    language_code: str = "ru",
) -> tuple[str, bool]:
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(
            DetectIntentRequest(
                session=session,
                query_input=query_input,
            ),
        )
        return response.query_result.fulfillment_text, response.query_result.intent.is_fallback
    except Exception as e:
        logger.error(e, exc_info=True)
        return "Неожиданная ошибка. Повторите попытку позже", True


def create_intent(
    project_id: str,
    display_name: str,
    training_phrases_parts: list[str],
    message_texts: list[str],
) -> Intent:
    intents_client = dialogflow.IntentsClient()

    parent = dialogflow.AgentsClient.agent_path(project_id)
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
