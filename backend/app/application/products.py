from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.images import detect_image_format
from app.application.ports import ImageStorage, ProductRepository
from app.domain.product import InvalidProduct, Product, normalize_title

MAX_IMAGE_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ProductView:
    id: UUID
    title: str
    image_url: str
    created_at: datetime


class CreateProduct:
    def __init__(self, products: ProductRepository, images: ImageStorage) -> None:
        self._products = products
        self._images = images

    async def execute(self, title: str, image: bytes) -> ProductView:
        title = normalize_title(title)
        if not image:
            raise InvalidProduct("Нужна фотография товара")
        if len(image) > MAX_IMAGE_SIZE:
            raise InvalidProduct(f"Фото больше {MAX_IMAGE_SIZE // (1024 * 1024)} МБ")
        image_format = detect_image_format(image)
        if image_format is None:
            raise InvalidProduct("Поддерживаются только JPEG, PNG и WebP")

        product_id = uuid4()
        product = Product(
            id=product_id,
            title=title,
            image_key=f"{product_id}.{image_format.extension}",
            created_at=datetime.now(UTC),
        )
        await self._images.upload(product.image_key, image, image_format.content_type)
        await self._products.add(product)
        return to_view(product, self._images)


class ListProducts:
    def __init__(self, products: ProductRepository, images: ImageStorage) -> None:
        self._products = products
        self._images = images

    async def execute(self, limit: int, offset: int) -> list[ProductView]:
        products = await self._products.list_recent(limit=limit, offset=offset)
        return [to_view(product, self._images) for product in products]


def to_view(product: Product, images: ImageStorage) -> ProductView:
    return ProductView(
        id=product.id,
        title=product.title,
        image_url=images.public_url(product.image_key),
        created_at=product.created_at,
    )
