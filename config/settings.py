from typing import Self

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseModel):
    token: SecretStr
    chat_id: int

    @property
    def bot_token(self) -> str:
        return self.token.get_secret_value()


class VKSettings(BaseModel):
    token: SecretStr
    group_id: int

    @property
    def api_token(self) -> str:
        return self.token.get_secret_value()


class DialogflowSettings(BaseModel):
    project_id: str


class AppSettings(BaseSettings):
    telegram: TelegramSettings
    vk: VKSettings
    dialogflow: DialogflowSettings

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file="../.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @classmethod
    def load(cls) -> Self:
        return cls()
