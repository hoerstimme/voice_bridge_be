import subprocess
from tempfile import NamedTemporaryFile

import httpx
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from starlette import status
from starlette.responses import StreamingResponse, Response

from voice_bridge_be.common import get_eleven_labs_api_key
from voice_bridge_be.services.text_to_speach_el import get_voice_id

app = APIRouter()

STS_MODEL_ID = "eleven_multilingual_sts_v2"
SUPPORTED_AUDIO_TYPES = ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "application/octet-stream"]


@app.post("/convert_voice_stream_bytes")
async def convert_voice(
    #voice_name: str = Form(...),
    audio_file: UploadFile = File(...),
    eleven_labs_api_key: str = Depends(get_eleven_labs_api_key)
):
    voice_name = "karl"
    voice_id = get_voice_id(voice_name)

    if audio_file.content_type not in SUPPORTED_AUDIO_TYPES:
        print(audio_file.content_type)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}"
        )


    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}"
    headers = {
        "xi-api-key": get_eleven_labs_api_key(),
    }

    files = {
        "audio": (audio_file.filename, await audio_file.read(), audio_file.content_type),
        "model_id": (None, STS_MODEL_ID)
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, files=files)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        audio_bytes = b"".join([chunk async for chunk in response.aiter_bytes()])
        print(f"Audio size: {len(audio_bytes)} bytes")

        async def audio_generator():
            async for chunk in response.aiter_bytes():
                yield chunk

        return StreamingResponse(
            content=audio_generator(),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=output.mp3"}
        )



@app.post("/convert_voice_full_audio")
async def convert_voice_full_audio(
    audio_file: UploadFile = File(...),
    eleven_labs_api_key: str = Depends(get_eleven_labs_api_key)
):
    voice_name = "karl"
    voice_id = get_voice_id(voice_name)

    if audio_file.content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}"
        )

    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}"
    headers = {
        "xi-api-key": eleven_labs_api_key,
    }

    files = {
        "audio": (audio_file.filename, await audio_file.read(), audio_file.content_type),
        "model_id": (None, STS_MODEL_ID)
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, files=files)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        audio_bytes = await response.aread()
        print(f"Audio size: {len(audio_bytes)} bytes")

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=output.mp3"}
        )


@app.post("/convert_voice_full_audio_webm")
async def convert_voice_full_audio(
    audio_file: UploadFile = File(...),
    eleven_labs_api_key: str = Depends(get_eleven_labs_api_key)
):
    voice_name = "karl"
    voice_id = get_voice_id(voice_name)

    if audio_file.content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}"
        )

    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}"
    headers = {
        "xi-api-key": eleven_labs_api_key,
    }

    files = {
        "audio": (audio_file.filename, await audio_file.read(), audio_file.content_type),
        "model_id": (None, STS_MODEL_ID)
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, files=files)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        mp3_bytes = await response.aread()
        print(f"Original MP3 size: {len(mp3_bytes)} bytes")

        try:
            webm_bytes = await mp3_to_webm(mp3_bytes)
            print(f"Converted WebM size: {len(webm_bytes)} bytes")
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"FFmpeg conversion failed: {e}")

        return Response(
            content=webm_bytes,
            media_type="audio/webm",
            headers={"Content-Disposition": "inline; filename=output.webm"}
        )


async def mp3_to_webm(mp3_bytes: bytes) -> bytes:
    with NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_file, \
         NamedTemporaryFile(delete=False, suffix=".webm") as webm_file:

        mp3_file.write(mp3_bytes)
        mp3_file.flush()

        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_file.name, "-c:a", "libopus", "-b:a", "96k", webm_file.name
        ], check=True)

        return open(webm_file.name, "rb").read()