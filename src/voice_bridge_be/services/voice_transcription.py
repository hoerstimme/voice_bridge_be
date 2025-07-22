import os
import tempfile

from fastapi import HTTPException
from openai import OpenAI, AsyncOpenAI

from voice_bridge_be import logger
from voice_bridge_be.common import get_open_ai_key

OPEN_AI_CLIENT = OpenAI(api_key=get_open_ai_key())
ASYNC_OPEN_AI_CLIENT = AsyncOpenAI(api_key=get_open_ai_key())
# .with_streaming_response
#
# The above interface eagerly reads the full response body when you make the request, which may not always be what you want.
#
# To stream the response body, use .with_streaming_response instead, which requires a context manager and only reads the response body once you call .read(), .text(), .json(), .iter_bytes(), .iter_text(), .iter_lines() or .parse(). In the async client, these are async methods.
#
# As such, .with_streaming_response methods return a different APIResponse object, and the async client returns an AsyncAPIResponse object.
#
# with client.chat.completions.with_streaming_response.create(
#     messages=[
#         {
#             "role": "user",
#             "content": "Say this is a test",
#         }
#     ],
#     model="gpt-4o",
# ) as response:
#     print(response.headers.get("X-My-Header"))
#
#     for line in response.iter_lines():
#         print(line)
#
# The context manager is required so that the response will reliably be closed.
def transcribe(file: bytes):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        temp_file.write(file)
        temp_file.seek(0)

        file_tuple = (temp_file.name.split("/")[-1], temp_file)
        logger.info("Temporary file created for transcription")

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
    return response.replace('\n', '')


async def transcribe_with_streaming(file: bytes):
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        temp_file.write(file)
        temp_file.seek(0)

        logger.info("Temporary file created for streaming transcription")
        file_tuple = (temp_file.name.split("/")[-1], temp_file)

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