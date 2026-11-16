from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from apps.api.app.models.entities import MediaType

class MediaAssetResponse(BaseModel):
    id: str
    owner_user_id: str
    storage_key: str
    original_filename: str
    detected_mime_type: str
    media_type: MediaType
    file_size_bytes: int
    sha256: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
