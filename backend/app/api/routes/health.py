import socket
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session

router = APIRouter(tags=["health"])

INSTANCE = socket.gethostname()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "instance": INSTANCE}


@router.get("/ready")
async def ready(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ready", "instance": INSTANCE}
