import pytest

from app.application.products import MAX_IMAGE_SIZE, CreateProduct, ListProducts
from app.domain.product import InvalidProduct
from tests.fakes import JPEG_BYTES, PNG_BYTES, InMemoryImageStorage, InMemoryProductRepository


@pytest.fixture
def repo() -> InMemoryProductRepository:
    return InMemoryProductRepository()


@pytest.fixture
def storage() -> InMemoryImageStorage:
    return InMemoryImageStorage()


async def test_create_product_saves_image_and_record(repo, storage):
    view = await CreateProduct(repo, storage).execute(title="  Кружка   белая ", image=PNG_BYTES)

    assert view.title == "Кружка белая"
    assert view.image_url == f"/media/{view.id}.png"
    assert storage.objects[f"{view.id}.png"] == (PNG_BYTES, "image/png")
    assert [p.id for p in repo.items] == [view.id]


@pytest.mark.parametrize(
    ("title", "image", "message"),
    [
        ("   ", JPEG_BYTES, "пустым"),
        ("x" * 256, JPEG_BYTES, "длиннее"),
        ("Кружка", b"", "Нужна фотография"),
        ("Кружка", b"GIF89a" + b"\x00" * 16, "JPEG, PNG и WebP"),
        ("Кружка", b"\xff\xd8\xff" + b"\x00" * MAX_IMAGE_SIZE, "МБ"),
    ],
)
async def test_create_product_rejects_invalid_input(repo, storage, title, image, message):
    with pytest.raises(InvalidProduct, match=message):
        await CreateProduct(repo, storage).execute(title=title, image=image)

    assert repo.items == []
    assert storage.objects == {}


async def test_list_products_returns_newest_first(repo, storage):
    create = CreateProduct(repo, storage)
    first = await create.execute(title="Первый", image=JPEG_BYTES)
    second = await create.execute(title="Второй", image=JPEG_BYTES)

    views = await ListProducts(repo, storage).execute(limit=10, offset=0)

    assert [v.id for v in views] == [second.id, first.id]
    assert views[0].image_url == f"/media/{second.id}.jpg"
