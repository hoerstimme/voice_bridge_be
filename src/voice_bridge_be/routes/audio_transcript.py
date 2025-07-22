import time

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from starlette import status
from starlette.responses import StreamingResponse

from voice_bridge_be import logger
from voice_bridge_be.common import get_open_ai_key
from voice_bridge_be.services.voice_transcription import transcribe, transcribe_with_streaming

app = APIRouter()


@app.post(
    "/voice_transcription",
    status_code=status.HTTP_201_CREATED
)
async def voice_to_text_processing(
        audio: UploadFile = File(None),
        open_ai_key: str = Depends(get_open_ai_key)
):
    logger.info("Received request for voice to text processing")
    if audio is None:
        logger.error("Audio file not provided")
        raise HTTPException(status_code=400, detail="Audio file must be provided")

    text = transcribe(file=audio.file.read())
    logger.info("Transcription successful")

    return text


@app.post(
    "/voice_transcription_stream",
    status_code=status.HTTP_201_CREATED
)
async def voice_to_text_streaming(
        audio: UploadFile = File(None),
        open_ai_key: str = Depends(get_open_ai_key)
):
    logger.info("Received request for voice to text streaming processing")
    if audio is None:
        logger.error("Audio file not provided")
        raise HTTPException(status_code=400, detail="Audio file must be provided")

    try:
        response_generator = transcribe_with_streaming(await audio.read())
    except Exception as e:
        logger.error(f"Streaming transcription failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during transcription")

    return StreamingResponse(response_generator, media_type="text/plain")
