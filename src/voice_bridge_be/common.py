from openai import OpenAI
from pydantic_settings import BaseSettings


import openai

from voice_bridge_be import PACKAGE_ROOT


class Settings(BaseSettings):
    openai_api_key: str
    eleven_labs_api_key: str
    eleven_labs_url: str

    class Config:
        env_file = "../../../.env"
        env_file_encoding = "utf-8"


def get_settings(env_path=None):
    if env_path is None:
        env_path = PACKAGE_ROOT / ".env"
    settings = Settings(_env_file=env_path, _env_file_encoding="utf-8")
    return settings

def get_database_url(env_path=None) -> str:
    if env_path is None:
        env_path = PACKAGE_ROOT / ".env"
    settings = Settings(_env_file=env_path, _env_file_encoding="utf-8")
    url = (
        f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}@{settings.db_host}:"
        f"{settings.db_port}/{settings.ai_postgres_db}"
    )
    return url

def get_open_ai_key():
    openai.api_key = get_settings().openai_api_key
    return openai.api_key


def get_eleven_labs_api_key():
    eleven_labs_api_key = get_settings().eleven_labs_api_key
    return eleven_labs_api_key


client = OpenAI(api_key=get_open_ai_key())
