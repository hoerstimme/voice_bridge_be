from pydantic import BaseModel


class AvailableVoices(BaseModel):
    voices: list[str]

