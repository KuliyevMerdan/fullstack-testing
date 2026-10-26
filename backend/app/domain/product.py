from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

MAX_TITLE_LENGTH = 255


class InvalidProduct(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Product:
    id: UUID
    title: str
    image_key: str
    created_at: datetime


def normalize_title(raw: str) -> str:
    title = " ".join(raw.split())
    if not title:
        raise InvalidProduct("Название товара не может быть пустым")
    if len(title) > MAX_TITLE_LENGTH:
        raise InvalidProduct(f"Название товара длиннее {MAX_TITLE_LENGTH} символов")
    return title
