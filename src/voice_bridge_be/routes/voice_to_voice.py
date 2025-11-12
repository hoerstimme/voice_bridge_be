# Ownership & License Notice
#
# All code and related assets in this file are the intellectual property of
# sinceare UG (haftungsbeschränkt), Berlin, Germany.
#
# Released under the PolyForm Noncommercial License 1.0.0:
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# - You may view, clone, and modify this code for personal, academic, or research use.
# - Commercial use, sale, or integration in commercial applications is prohibited.
# - You must include this license notice in any copies or derivatives.
#
# For commercial or partnership inquiries, contact: ps@sinceare.com
#
import subprocess
from tempfile import NamedTemporaryFile

import httpx
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from starlette import status
from starlette.responses import StreamingResponse, Response

from voice_bridge_be import logger
from voice_bridge_be.common import get_eleven_labs_api_key
from voice_bridge_be.services.text_to_speach_el import get_voice_id

app = APIRouter()

STS_MODEL_ID = "eleven_multilingual_sts_v2"
SUPPORTED_AUDIO_TYPES = ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "application/octet-stream"]

@app.post("/convert_voice_stream_bytes_webm")
async def convert_voice_full_audio(
    voice_name: str = Form(...),
    audio_file: UploadFile = File(...),
    eleven_labs_api_key: str = Depends(get_eleven_labs_api_key)
):
    voice_id = get_voice_id(voice_name)
    check_content_type_of_audio_file(audio_file=audio_file)

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
            logger.error(f"Failed with processing request with ElevenLabs API. Status code: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        mp3_bytes = await response.aread()
        logger.info(f"Original MP3 size: {len(mp3_bytes)} bytes")

        try:
            webm_bytes = await mp3_to_webm(mp3_bytes)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
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


def check_content_type_of_audio_file(audio_file: UploadFile):
    if audio_file.content_type not in SUPPORTED_AUDIO_TYPES:
        logger.error(
            f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}")

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}"
        )
import subprocess
from tempfile import NamedTemporaryFile

import httpx
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from starlette import status
from starlette.responses import StreamingResponse, Response

from voice_bridge_be import logger
from voice_bridge_be.common import get_eleven_labs_api_key
from voice_bridge_be.services.text_to_speach_el import get_voice_id

app = APIRouter()

STS_MODEL_ID = "eleven_multilingual_sts_v2"
SUPPORTED_AUDIO_TYPES = ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "application/octet-stream"]

@app.post("/convert_voice_stream_bytes_webm")
async def convert_voice_full_audio(
    voice_name: str = Form(...),
    audio_file: UploadFile = File(...),
    eleven_labs_api_key: str = Depends(get_eleven_labs_api_key)
):
    voice_id = get_voice_id(voice_name)
    check_content_type_of_audio_file(audio_file=audio_file)

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
            logger.error(f"Failed with processing request with ElevenLabs API. Status code: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        mp3_bytes = await response.aread()
        logger.info(f"Original MP3 size: {len(mp3_bytes)} bytes")

        try:
            webm_bytes = await mp3_to_webm(mp3_bytes)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
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


def check_content_type_of_audio_file(audio_file: UploadFile):
    if audio_file.content_type not in SUPPORTED_AUDIO_TYPES:
        logger.error(
            f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}")

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format '{audio_file.content_type}'. Supported formats: {SUPPORTED_AUDIO_TYPES}"
        )