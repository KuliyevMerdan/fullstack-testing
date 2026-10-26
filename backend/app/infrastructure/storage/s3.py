from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3

from app.config import Settings


class S3ImageStorage:
    def __init__(self, client: Any, bucket: str, public_base_url: str) -> None:
        self._client = client
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        await self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )

    def public_url(self, key: str) -> str:
        return f"{self._public_base_url}/{key}"


@asynccontextmanager
async def create_s3_client(settings: Settings) -> AsyncIterator[Any]:
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
        region_name="us-east-1",
    ) as client:
        yield client
