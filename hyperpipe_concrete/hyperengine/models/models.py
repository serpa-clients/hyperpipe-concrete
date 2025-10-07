from typing import Any
from pydantic import BaseModel

class Origin(BaseModel):
    mime_type: str = ""
    file_type: str = ""
    source: str = ""
    reference: str = ""
    reference_id: str = ""

class qChunk(BaseModel):
    uid: str
    text: str
    headers: str = ""
    pages: list[int] = []
    metadata: None | dict[str, Any] = None

class qTracker(BaseModel):
    data: str = ""
    chunks: list[qChunk] = []
    name: str = ""
    origin: Origin = Origin()
    metadata: None | dict[str, Any] = None