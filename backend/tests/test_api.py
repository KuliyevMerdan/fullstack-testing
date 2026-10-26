import httpx
import pytest

from app.api.deps import get_create_product, get_list_products
from app.application.products import CreateProduct, ListProducts
from app.config import get_settings
from app.main import create_app
from tests.fakes import JPEG_BYTES, InMemoryImageStorage, InMemoryProductRepository

TOKEN = "test-service-token"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://unused/unused")
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://unused")
    monkeypatch.setenv("S3_ACCESS_KEY", "unused")
    monkeypatch.setenv("S3_SECRET_KEY", "unused")
    monkeypatch.setenv("S3_BUCKET", "unused")
    monkeypatch.setenv("SERVICE_TOKEN", TOKEN)
    get_settings.cache_clear()

    repo, storage = InMemoryProductRepository(), InMemoryImageStorage()
    app = create_app()
    app.dependency_overrides[get_create_product] = lambda: CreateProduct(repo, storage)
    app.dependency_overrides[get_list_products] = lambda: ListProducts(repo, storage)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _form(title: str = "Кружка", image: bytes = JPEG_BYTES):
    return {"data": {"title": title}, "files": {"image": ("photo.jpg", image, "image/jpeg")}}


async def test_create_and_list(client):
    async with client:
        created = await client.post(
            "/api/products", headers={"Authorization": f"Bearer {TOKEN}"}, **_form()
        )
        listed = await client.get("/api/products")

    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Кружка"
    assert body["image_url"] == f"/media/{body['id']}.jpg"
    assert listed.status_code == 200
    assert [p["id"] for p in listed.json()] == [body["id"]]


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}])
async def test_create_requires_service_token(client, headers):
    async with client:
        response = await client.post("/api/products", headers=headers, **_form())

    assert response.status_code == 401


async def test_create_returns_422_with_readable_message(client):
    async with client:
        response = await client.post(
            "/api/products",
            headers={"Authorization": f"Bearer {TOKEN}"},
            **_form(image=b"not an image"),
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Поддерживаются только JPEG, PNG и WebP"}
