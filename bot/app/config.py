from functools import lru_cache
from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    bot_token: SecretStr
    public_url: str
    webhook_secret: SecretStr
    webhook_path: str = "/tg/webhook"
    admin_ids: Annotated[frozenset[int], NoDecode] = frozenset()

    api_internal_url: str
    service_token: SecretStr

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _split_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return frozenset(int(part) for part in value.split(",") if part.strip())
        return value

    @property
    def webhook_url(self) -> str:
        return self.public_url.rstrip("/") + self.webhook_path

    @property
    def webapp_url(self) -> str:
        return self.public_url.rstrip("/") + "/"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
