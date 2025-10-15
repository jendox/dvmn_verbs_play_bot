import logging
import random
from typing import Any

import anyio
import httpx

from bots.vk.http import get_async_http_client
from bots.vk.models import (
    POLL_WAIT_TIME,
    LongPollError,
    LongPollHistoryOutdated,
    LongPollInfoLost,
    LongPollKeyExpired,
    LongPollResponse,
    LongPollServer,
    VKApiMethod,
)
from dialogflow import DetectIntentHandler

__all__ = (
    "VKBot",
    "VK_LOGGER_NAME",
)

VK_LOGGER_NAME = "vk"
API_URL = "https://api.vk.com/method"
API_VERSION = "5.199"
POLL_EXC_SLEEP_TIME = 5.0


class VKBot:
    def __init__(
        self,
        api_token: str,
        group_id: int,
        detect_intent: DetectIntentHandler,
    ) -> None:
        self._api_token = api_token
        self._group_id = group_id
        self._http_client: httpx.AsyncClient | None = None
        self._detect_intent = detect_intent
        self.logger = logging.getLogger(VK_LOGGER_NAME)

    async def _request(self, method: VKApiMethod, **params) -> dict[str, Any]:
        url = f"/{method.value}"
        params["access_token"] = self._api_token
        params["v"] = API_VERSION
        response = await self._http_client.post(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _get_long_poll_server(self) -> LongPollServer:
        server_data = await self._request(
            VKApiMethod.GET_LONG_POLL_SERVER,
            group_id=self._group_id,
        )
        return LongPollServer.parse(server_data)

    async def _get_updates(self, server: LongPollServer) -> LongPollResponse:
        url = f"{server.url}?{server.urlencode_params()}"
        response = await self._http_client.get(url)
        response.raise_for_status()
        return LongPollResponse.parse(response.json())

    async def _send_message(self, user_id: int, message: str):
        await self._request(
            VKApiMethod.SEND_MESSAGE,
            user_id=user_id,
            message=message,
            random_id=random.randint(1, 1000),
        )

    async def long_polling(self):
        server = await self._get_long_poll_server()
        while True:
            try:
                response = await self._get_updates(server)
                server.ts = response.ts
                for update in response.get_new_message_updates():
                    reply_text, is_fallback = await self._detect_intent(update.user_id, update.text)
                    if not is_fallback:
                        await self._send_message(update.user_id, reply_text)
            except LongPollHistoryOutdated as e:
                server.ts = e.new_ts
                continue
            except (LongPollKeyExpired, LongPollInfoLost):
                server = await self._get_long_poll_server()
                continue
            except LongPollError:
                raise
            except Exception as e:
                self.logger.error(e, exc_info=True)
                await anyio.sleep(POLL_EXC_SLEEP_TIME)

    async def run(self):
        try:
            async with get_async_http_client(API_URL, POLL_WAIT_TIME) as client:
                self._http_client = client
                await self.long_polling()
        except LongPollError as e:
            self.logger.error(e, exc_info=True)
