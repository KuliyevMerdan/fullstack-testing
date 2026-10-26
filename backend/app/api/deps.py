import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import ImageStorage, ProductRepository
from app.application.products import CreateProduct, ListProducts
from app.config import Settings, get_settings
from app.infrastructure.db.repositories import SqlAlchemyProductRepository
from app.infrastructure.storage.s3 import S3ImageStorage


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_product_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductRepository:
    return SqlAlchemyProductRepository(session)


def get_image_storage(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> ImageStorage:
    return S3ImageStorage(request.app.state.s3_client, settings.s3_bucket, settings.media_base_url)


def get_create_product(
    products: Annotated[ProductRepository, Depends(get_product_repository)],
    images: Annotated[ImageStorage, Depends(get_image_storage)],
) -> CreateProduct:
    return CreateProduct(products, images)


def get_list_products(
    products: Annotated[ProductRepository, Depends(get_product_repository)],
    images: Annotated[ImageStorage, Depends(get_image_storage)],
) -> ListProducts:
    return ListProducts(products, images)


_bearer = HTTPBearer(auto_error=False)


def require_service_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    expected = settings.service_token.get_secret_value()
    if credentials is None or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный сервисный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
