from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.product import Product
from app.infrastructure.db.models import ProductModel


class SqlAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, product: Product) -> None:
        self._session.add(
            ProductModel(
                id=product.id,
                title=product.title,
                image_key=product.image_key,
                created_at=product.created_at,
            )
        )
        await self._session.commit()

    async def list_recent(self, limit: int, offset: int) -> list[Product]:
        rows = await self._session.scalars(
            select(ProductModel)
            .order_by(ProductModel.created_at.desc(), ProductModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(row) for row in rows]


def _to_entity(row: ProductModel) -> Product:
    return Product(id=row.id, title=row.title, image_key=row.image_key, created_at=row.created_at)
