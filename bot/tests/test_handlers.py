from datetime import datetime

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import AnswerCallbackQuery, GetFile, SendMessage, SetWebhook
from aiogram.types import Chat, File, Message, Update

from app.config import Settings
from app.main import create_dispatcher, on_startup
from app.services.catalog_api import CatalogApiError

ADMIN, USER = 111, 222
IMAGE = b"\xff\xd8\xff" + b"\x00" * 16
PHOTO = [
    {"file_id": "small", "file_unique_id": "s", "width": 90, "height": 90},
    {"file_id": "big", "file_unique_id": "b", "width": 800, "height": 800},
]


class FakeTelegramSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.sent: list[SendMessage] = []
        self.requested_files: list[str] = []

    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, GetFile):
            self.requested_files.append(method.file_id)
            return File(file_id=method.file_id, file_unique_id="u", file_path="photos/p.jpg")
        if isinstance(method, SendMessage):
            self.sent.append(method)
            chat = Chat(id=method.chat_id, type="private")
            return Message(message_id=1, date=datetime.now(), chat=chat, text=method.text)
        if isinstance(method, AnswerCallbackQuery):
            return True
        raise AssertionError(f"Неожиданный вызов {type(method).__name__}")

    async def stream_content(self, url, headers=None, timeout=30, chunk_size=65536, raise_for_status=True):
        yield IMAGE

    async def close(self) -> None:
        pass


class FakeCatalogApi:
    def __init__(self, error: CatalogApiError | None = None) -> None:
        self.created: list[tuple[str, bytes]] = []
        self.error = error

    async def create_product(self, title: str, image: bytes) -> dict:
        if self.error:
            raise self.error
        self.created.append((title, image))
        return {"title": title}


def message_update(user: int, **fields) -> dict:
    message = {
        "message_id": 1,
        "date": 0,
        "chat": {"id": user, "type": "private"},
        "from": {"id": user, "is_bot": False, "first_name": "T"},
    }
    return {"update_id": 1, "message": {**message, **fields}}


@pytest.fixture
def settings() -> Settings:
    return Settings(
        bot_token="42:TEST",
        public_url="https://catalog.example",
        webhook_secret="secret",
        admin_ids=str(ADMIN),
        api_internal_url="http://api",
        service_token="token",
    )


@pytest.fixture
def session() -> FakeTelegramSession:
    return FakeTelegramSession()


@pytest.fixture
def feed(settings, session):
    async def _feed(raw: dict, api: FakeCatalogApi | None = None) -> list[SendMessage]:
        bot = Bot("42:TEST", session=session)
        dispatcher = create_dispatcher(settings, api or FakeCatalogApi())
        await dispatcher.feed_update(bot, Update.model_validate(raw, context={"bot": bot}))
        return session.sent

    return _feed


def buttons(message: SendMessage) -> list[str]:
    return [button.text for row in message.reply_markup.inline_keyboard for button in row]


@pytest.mark.parametrize(
    ("user", "expected"),
    [(USER, ["Открыть каталог"]), (ADMIN, ["Открыть каталог", "Создать товар"])],
)
async def test_greeting_offers_mini_app(feed, user, expected):
    [reply] = await feed(message_update(user, text="/start"))

    assert reply.text == "У меня есть товар"
    assert buttons(reply) == expected
    assert reply.reply_markup.inline_keyboard[0][0].web_app.url == "https://catalog.example/"


async def test_admin_creates_product_from_largest_photo(feed, session):
    api = FakeCatalogApi()

    [reply] = await feed(message_update(ADMIN, photo=PHOTO, caption="Кружка"), api)

    assert api.created == [("Кружка", IMAGE)]
    assert session.requested_files == ["big"]
    assert reply.text == "Товар «Кружка» добавлен в каталог."


async def test_api_validation_error_is_shown_to_admin(feed):
    api = FakeCatalogApi(CatalogApiError("422", user_message="Поддерживаются только JPEG, PNG и WebP"))

    [reply] = await feed(message_update(ADMIN, photo=PHOTO, caption="Кружка"), api)

    assert reply.text == "Поддерживаются только JPEG, PNG и WebP"


async def test_photo_without_caption_asks_for_title(feed):
    api = FakeCatalogApi()

    [reply] = await feed(message_update(ADMIN, photo=PHOTO), api)

    assert api.created == []
    assert reply.text == "Добавьте название товара в подпись к фото."


async def test_non_admin_cannot_create_product(feed):
    api = FakeCatalogApi()

    [reply] = await feed(message_update(USER, photo=PHOTO, caption="Кружка"), api)

    assert api.created == []
    assert reply.text == "У меня есть товар"


class FloodControlledSession(FakeTelegramSession):
    def __init__(self) -> None:
        super().__init__()
        self.webhooks: list[SetWebhook] = []

    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, SetWebhook):
            self.webhooks.append(method)
            if len(self.webhooks) == 1:
                raise TelegramRetryAfter(method=method, message="Too Many Requests", retry_after=0)
            return True
        return await super().make_request(bot, method, timeout)


async def test_startup_retries_set_webhook_after_flood_control(settings):
    session = FloodControlledSession()
    bot = Bot("42:TEST", session=session)

    await on_startup(bot, create_dispatcher(settings, FakeCatalogApi()), settings)

    assert len(session.webhooks) == 2
    assert session.webhooks[-1].url == settings.webhook_url
    assert session.webhooks[-1].secret_token == "secret"
