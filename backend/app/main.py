from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes import health, products
from app.config import get_settings
from app.domain.product import InvalidProduct
from app.infrastructure.db.session import create_engine, create_session_factory
from app.infrastructure.storage.s3 import create_s3_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with AsyncExitStack() as stack:
        engine = create_engine(settings.database_url)
        stack.push_async_callback(engine.dispose)
        app.state.session_factory = create_session_factory(engine)
        app.state.s3_client = await stack.enter_async_context(create_s3_client(settings))
        yield


async def invalid_product_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})


def create_app() -> FastAPI:
    app = FastAPI(
        title="Catalog API",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_exception_handler(InvalidProduct, invalid_product_handler)
    app.include_router(health.router, prefix="/api")
    app.include_router(products.router, prefix="/api")
    return app


app = create_app()
