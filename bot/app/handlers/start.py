from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import Settings
from app.handlers.admin import CREATE_PRODUCT_CALLBACK


def greeting_keyboard(webapp_url: str, is_admin: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Открыть каталог", web_app=WebAppInfo(url=webapp_url))]]
    if is_admin:
        rows.append(
            [InlineKeyboardButton(text="Создать товар", callback_data=CREATE_PRODUCT_CALLBACK)]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def greet(message: Message, settings: Settings) -> None:
    is_admin = message.from_user is not None and message.from_user.id in settings.admin_ids
    await message.answer(
        "У меня есть товар",
        reply_markup=greeting_keyboard(settings.webapp_url, is_admin),
    )


def create_router() -> Router:
    router = Router(name="start")
    router.message.register(greet)
    return router
