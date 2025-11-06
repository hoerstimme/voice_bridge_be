import os
import tempfile

# new Start for audio resampling for fixed sample rate
import io
import soundfile as sf
import resampy
import shutil
#new End

from fastapi import HTTPException
from openai import OpenAI, AsyncOpenAI

from voice_bridge_be import logger
from voice_bridge_be.common import get_open_ai_key

OPEN_AI_CLIENT = OpenAI(api_key=get_open_ai_key())
ASYNC_OPEN_AI_CLIENT = AsyncOpenAI(api_key=get_open_ai_key())

# OLD Transcribe function commented out
# The context manager is required so that the response will reliably be closed.
""" def transcribe(file: bytes):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        temp_file.write(file)
        temp_file.seek(0)

        # Debug: Kopiere die temporäre Datei für Analyse
        import shutil
        debug_path = "/tmp/debug_transcribe.mp4"
        shutil.copy(temp_file.name, debug_path)
        logger.info(f"Temporary file created for transcription: {temp_file.name}")
        logger.info(f"Debug copy saved to: {debug_path}")

        file_tuple = (temp_file.name.split("/")[-1], temp_file)

        try:
            logger.info("Starting transcription")
            response = OPEN_AI_CLIENT.audio.transcriptions.create(
                model="whisper-1", file=file_tuple,  response_format="text", language="DE"
            )
        except Exception as e:
            logger.error(f"An error occurred during transcription: {e}")
            raise HTTPException(
                status_code=500, detail="An error occurred during transcription"
            ) from e
    return response.replace('\n', '') """
# OLD Transcribe function commented out end

# NEW streaming transcription function with Resamplin Start
def transcribe(file: bytes):
    # Read the audio file from bytes
    audio_bytes = io.BytesIO(file)
    data, samplerate = sf.read(audio_bytes)
    target_sr = 16000

    # Resample if necessary
    if samplerate != target_sr:
        data = resampy.resample(data, samplerate, target_sr)
        samplerate = target_sr

    # Write the (possibly resampled) audio to a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        sf.write(temp_file, data, samplerate)
        temp_file.seek(0)
        file_tuple = (temp_file.name.split("/")[-1], temp_file)
        logger.info("Temporary file created for transcription")

        try:
            logger.info("Starting transcription")
            response = OPEN_AI_CLIENT.audio.transcriptions.create(
                model="whisper-1", file=file_tuple, response_format="text", language="DE"
            )
        except Exception as e:
            logger.error(f"An error occurred during transcription: {e}")
            raise HTTPException(
                status_code=500, detail="An error occurred during transcription"
            ) from e
    return response.replace('\n', '')
#New streaming transcription function End

async def transcribe_with_streaming(file: bytes):
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        temp_file.write(file)
        temp_file.seek(0)

        logger.info("Temporary file created for streaming transcription")
        file_tuple = (temp_file.name.split("/")[-1], temp_file)
        
        # For debugging: save a copy of the temp file
       # shutil.copy(temp_file.name, "/tmp/debug.wav")

        try:
            logger.info("Starting streaming transcription")
            stream = await ASYNC_OPEN_AI_CLIENT.audio.transcriptions.create(
                model="whisper-1", file=file_tuple, response_format="text", stream=True
            )
            logger.info("Stream initialized successfully.")
            async for event in stream:
                logger.info(f"Received stream event: {event}")
                yield event["text"] if "text" in event else event

        except Exception as e:
            logger.error(f"An error occurred during streaming transcription: {e}")
            raise HTTPException(
                status_code=500, detail="An error occurred during transcription"
            ) from e
    finally:
        # Ensure file cleanup
        temp_file.close()
        os.unlink(temp_file.name)