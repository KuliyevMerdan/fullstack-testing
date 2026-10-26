from app.domain.product import Product


class InMemoryProductRepository:
    def __init__(self) -> None:
        self.items: list[Product] = []

    async def add(self, product: Product) -> None:
        self.items.append(product)

    async def list_recent(self, limit: int, offset: int) -> list[Product]:
        ordered = sorted(self.items, key=lambda p: p.created_at, reverse=True)
        return ordered[offset : offset + limit]


class InMemoryImageStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    def public_url(self, key: str) -> str:
        return f"/media/{key}"


JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 16
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
