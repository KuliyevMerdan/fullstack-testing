from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.deps import get_create_product, get_list_products, require_service_token
from app.api.schemas import ProductOut
from app.application.products import MAX_IMAGE_SIZE, CreateProduct, ListProducts

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    use_case: Annotated[ListProducts, Depends(get_list_products)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProductOut]:
    products = await use_case.execute(limit=limit, offset=offset)
    return [ProductOut.model_validate(product) for product in products]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_service_token)],
)
async def create_product(
    use_case: Annotated[CreateProduct, Depends(get_create_product)],
    title: Annotated[str, Form()],
    image: Annotated[UploadFile, File()],
) -> ProductOut:
    data = await image.read(MAX_IMAGE_SIZE + 1)
    product = await use_case.execute(title=title, image=data)
    return ProductOut.model_validate(product)
