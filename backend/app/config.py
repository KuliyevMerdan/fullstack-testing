from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: SecretStr
    s3_bucket: str
    media_base_url: str = "/media"

    service_token: SecretStr


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
