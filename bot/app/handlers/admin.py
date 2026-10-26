import html
import logging
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.filters import IsAdmin
from app.services.catalog_api import CatalogApi, CatalogApiError

logger = logging.getLogger(__name__)

CREATE_PRODUCT_CALLBACK = "create_product"
INSTRUCTION = "Отправьте фото товара, а в подписи к нему укажите название."


async def create_product_command(message: Message) -> None:
    await message.answer(INSTRUCTION)


async def create_product_button(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(INSTRUCTION)


async def create_product(message: Message, bot: Bot, catalog_api: CatalogApi) -> None:
    assert message.photo is not None and message.caption is not None

    buffer = BytesIO()
    await bot.download(message.photo[-1], destination=buffer)

    try:
        product = await catalog_api.create_product(title=message.caption, image=buffer.getvalue())
    except CatalogApiError as exc:
        logger.warning("Не удалось создать товар: %s", exc)
        await message.reply(exc.user_message or "Не удалось сохранить товар, попробуйте ещё раз.")
        return

    await message.reply(f"Товар «{html.escape(product['title'])}» добавлен в каталог.")


async def photo_without_caption(message: Message) -> None:
    await message.reply("Добавьте название товара в подпись к фото.")


def create_router() -> Router:
    router = Router(name="admin")
    router.message.filter(IsAdmin())
    router.callback_query.filter(IsAdmin())
    router.message.register(create_product_command, Command("create"))
    router.message.register(create_product_command, F.text.casefold() == "создать товар")
    router.callback_query.register(create_product_button, F.data == CREATE_PRODUCT_CALLBACK)
    router.message.register(create_product, F.photo, F.caption)
    router.message.register(photo_without_caption, F.photo)
    return router
