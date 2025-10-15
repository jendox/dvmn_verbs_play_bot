from enum import Enum
from typing import Any, Self
from urllib.parse import urlencode

from pydantic import BaseModel, Field, ValidationError

POLL_WAIT_TIME = 25.0


class LongPollFailed(int, Enum):
    HISTORY_OUTDATED = 1
    KEY_EXPIRED = 2
    INFO_LOST = 3


class LongPollError(RuntimeError):
    """Базовое исключение для ошибок LongPoll"""


class LongPollHistoryOutdated(LongPollError):
    """История событий устарела (failed: 1) - нужно обновить ts"""

    def __init__(self, ts: str, message: str = "История событий устарела") -> None:
        self.new_ts = ts
        super().__init__(message)


class LongPollKeyExpired(LongPollError):
    """Истекло время действия ключа (failed: 2) - нужно получить новый сервер"""


class LongPollInfoLost(LongPollError):
    """Информация утрачена (failed: 3) - нужно получить новый сервер"""


class VKApiMethod(str, Enum):
    GET_LONG_POLL_SERVER = "groups.getLongPollServer"
    SEND_MESSAGE = "messages.send"


class MessageType(str, Enum):
    MESSAGE_NEW = "message_new"
    MESSAGE_REPLY = "message_reply"
    MESSAGE_EDIT = "message_edit"
    MESSAGE_ALLOW = "message_allow"
    MESSAGE_DENY = "message_deny"
    MESSAGE_TYPING_STATE = "message_typing_state"
    MESSAGE_EVENT = "message_event"


class LongPollServer(BaseModel):
    url: str = Field(alias="server")
    key: str
    ts: str
    act: str = "a_check"
    wait: float = POLL_WAIT_TIME

    def urlencode_params(self) -> str:
        return urlencode(self.model_dump(exclude={"url"}))

    @classmethod
    def parse(cls, server_data: dict[str, Any]) -> Self:
        error = server_data.get("error")
        if error:
            message = error.get("error_msg")
            raise LongPollError(f"Ошибка получения long poll server: {message}")
        return cls(**server_data["response"])


class UpdateMessage(BaseModel):
    id: int
    from_id: int
    text: str


class UpdateObject(BaseModel):
    message: UpdateMessage


class Update(BaseModel):
    type: MessageType
    object: UpdateObject

    @property
    def user_id(self) -> int:
        return self.object.message.from_id

    @property
    def text(self) -> str:
        return self.object.message.text


class LongPollResponse(BaseModel):
    ts: str
    updates: list[dict[str, Any]]

    def get_new_message_updates(self) -> list[Update]:
        new_updates = []
        for update in self.updates:
            if update.get("type") == MessageType.MESSAGE_NEW:
                try:
                    new_updates.append(Update(**update))
                except ValidationError:
                    pass
        return new_updates

    @classmethod
    def parse(cls, server_data: dict[str, Any]) -> Self:
        failed = server_data.get("failed")
        if failed == LongPollFailed.HISTORY_OUTDATED:
            raise LongPollHistoryOutdated(ts=server_data.get("ts"))
        if failed == LongPollFailed.KEY_EXPIRED:
            raise LongPollKeyExpired()
        if failed == LongPollFailed.INFO_LOST:
            raise LongPollInfoLost()
        return cls(**server_data)
