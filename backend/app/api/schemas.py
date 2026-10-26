from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    image_url: str
    created_at: datetime
