import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import Settings, get_settings
from app.handlers import admin, start
from app.services.catalog_api import CatalogApi

logger = logging.getLogger(__name__)

SET_WEBHOOK_ATTEMPTS = 5


async def on_startup(bot: Bot, dispatcher: Dispatcher, settings: Settings) -> None:
    for attempt in range(1, SET_WEBHOOK_ATTEMPTS + 1):
        try:
            await bot.set_webhook(
                url=settings.webhook_url,
                secret_token=settings.webhook_secret.get_secret_value(),
                allowed_updates=dispatcher.resolve_used_update_types(),
            )
            return
        except TelegramRetryAfter as error:
            if attempt == SET_WEBHOOK_ATTEMPTS:
                raise
            logger.warning("setWebhook: флуд-контроль, повтор через %s с", error.retry_after)
            await asyncio.sleep(error.retry_after)


async def on_shutdown(catalog_api: CatalogApi) -> None:
    await catalog_api.close()


def create_dispatcher(settings: Settings, catalog_api: CatalogApi) -> Dispatcher:
    dispatcher = Dispatcher(settings=settings, catalog_api=catalog_api)
    dispatcher.include_routers(admin.create_router(), start.create_router())
    return dispatcher


async def healthz(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app(settings: Settings) -> web.Application:
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    catalog_api = CatalogApi(settings.api_internal_url, settings.service_token.get_secret_value())
    dispatcher = create_dispatcher(settings, catalog_api)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/healthz", healthz)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.webhook_secret.get_secret_value(),
    ).register(app, path=settings.webhook_path)
    setup_application(app, dispatcher, bot=bot)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    web.run_app(create_app(get_settings()), host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
