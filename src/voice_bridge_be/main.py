import toml
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware

from voice_bridge_be import PACKAGE_ROOT
from voice_bridge_be.routes import text_to_speach_eleven_labs, audio_transcript


def get_project_version() -> str:
    with open(PACKAGE_ROOT / "pyproject.toml") as f:
        pyproject_data = toml.load(f)
    return pyproject_data["project"]["version"]


app = FastAPI(
    title="Voice Bridge",
    version=get_project_version(),  # type: ignore  # noqa
)

routers = [
    text_to_speach_eleven_labs.app,
    audio_transcript.app
]

for router in routers:
    app.include_router(router)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title,
    )


if __name__ == "__main__":
    uvicorn.run(
        "voice_bridge_be.main:app",
        host="127.0.0.1",
        port=8001,
        log_level="debug",
    )
