from contextvars import ContextVar

from google.cloud import dialogflow
from google.cloud.dialogflow_v2 import DetectIntentRequest

dialogflow_project_id: ContextVar[str] = ContextVar("DialogFlow Project ID")


async def get_response(
    project_id: str,
    session_id: int,
    text: str,
    language_code: str = "ru",
) -> str:
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
