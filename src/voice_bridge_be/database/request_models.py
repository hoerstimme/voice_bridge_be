from typing import Optional

from pydantic import BaseModel


class AudioRequest(BaseModel):
    text: Optional[str] = None
    voice: str
