import logging
import os
import random

import vk_api
from dotenv import load_dotenv
from vk_api.longpoll import Event, VkEventType, VkLongPoll
from vk_api.vk_api import VkApiMethod

import dialogflow
from logs import setup_logging

VK_LOGGER_NAME = "vk"

logger = logging.getLogger(VK_LOGGER_NAME)


def reply(event: Event, api: VkApiMethod, project_id: str):
    session_id = f"vk-{event.user_id}"
    try:
        text, is_fallback = dialogflow.detect_intent(project_id, session_id, event.text)
        if not is_fallback:
            api.messages.send(
                user_id=event.user_id,
                message=text,
                random_id=random.randint(1, 1_000_000),
            )
    except Exception as error:
        logger.error(f"Ошибка отправки ответа пользователю: {error}")


def main():
    load_dotenv()
    try:
        vk_token = os.environ["VK_TOKEN"]
        project_id = os.environ["DIALOGFLOW_PROJECT_ID"]
        tg_token = os.environ["TELEGRAM_TOKEN"]
        tg_chat_id = os.environ["TELEGRAM_CHAT_ID"]

        setup_logging(tg_token, tg_chat_id, VK_LOGGER_NAME)
        vk_session = vk_api.VkApi(token=vk_token)
        api = vk_session.get_api()
        long_poll = VkLongPoll(vk_session)

        for event in long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                reply(event, api, project_id)
    except KeyError as e:
        logger.error(f"Не настроены необходимые переменные окружения: {e}")
    except Exception as exc:
        logger.error(f"Неожиданное исключение: {exc}")
    except KeyboardInterrupt:
        logger.info("Завершено пользователем")


if __name__ == "__main__":
    main()
