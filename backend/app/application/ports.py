from typing import Protocol

from app.domain.product import Product


class ProductRepository(Protocol):
    async def add(self, product: Product) -> None: ...

    async def list_recent(self, limit: int, offset: int) -> list[Product]: ...


class ImageStorage(Protocol):
    async def upload(self, key: str, data: bytes, content_type: str) -> None: ...

    def public_url(self, key: str) -> str: ...
