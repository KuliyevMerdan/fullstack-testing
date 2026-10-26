import httpx


class CatalogApiError(Exception):
    def __init__(self, message: str, user_message: str | None = None) -> None:
        super().__init__(message)
        self.user_message = user_message


class CatalogApi:
    def __init__(self, base_url: str, service_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {service_token}"},
            timeout=httpx.Timeout(30.0),
        )

    async def create_product(self, title: str, image: bytes) -> dict:
        try:
            response = await self._client.post(
                "/api/products",
                data={"title": title},
                files={"image": ("photo.jpg", image)},
            )
        except httpx.HTTPError as exc:
            raise CatalogApiError(f"API недоступен: {exc!r}") from exc

        if response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
            detail = response.json().get("detail")
            raise CatalogApiError(f"422: {detail}", user_message=detail if isinstance(detail, str) else None)
        if response.is_error:
            raise CatalogApiError(f"API ответил {response.status_code}: {response.text[:200]}")
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
