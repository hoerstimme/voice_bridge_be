import base64
import json
import os
from typing import Optional

import websockets
from elevenlabs import ElevenLabs, stream
from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from voice_bridge_be import PACKAGE_ROOT, logger
from voice_bridge_be.common import get_eleven_labs_api_key
from voice_bridge_be.database.request_models import AudioRequest

VOICE_MAPPING = {
    "karl": "VO7pRycLkEn8V7IWzZ0r",
    "jessica": "g6xIsTj2HwM6VR4iXFCw",
    "test": "nPczCjzI2devNBz1zQrb"
}

DEFAULT_TEXT = """Guten Morgen!
Heute ist ein ganz normaler Tag. Ich bin gegen acht Uhr aufgewacht, habe einen Kaffee gemacht und ein bisschen Musik gehört. Danach bin ich eine Runde spazieren gegangen, weil das Wetter wirklich schön ist – sonnig, aber nicht zu heiß.
Jetzt sitze ich am Schreibtisch und arbeite an ein paar Projekten. Später werde ich vielleicht einkaufen gehen und etwas Leckeres zum Abendessen kochen.
Ich überlege, ob ich heute Abend noch einen Film schaue oder ein Buch lese. Mal sehen, wie ich mich fühle.
Auf jeden Fall versuche ich, den Tag ruhig und entspannt zu gestalten."""

EL_CLIENT = ElevenLabs(api_key=get_eleven_labs_api_key())
MODEL_ID = "eleven_multilingual_v2"


def produce_stream_audio(request: AudioRequest):
    logger.info("Received request for tts processing")
    if not request.text:
        default_file_map = {
            "jessica": os.path.join(PACKAGE_ROOT, "src/voice_bridge_be/services/audio_files/default_jessica.mp3"),
            "karl": os.path.join(PACKAGE_ROOT, "src/voice_bridge_be/services/audio_files/default_karl.mp3"),
        }

        default_file = default_file_map.get(request.voice.lower())

        if default_file:
            logger.info("Return default file.")
            return FileResponse(
                default_file,
                media_type="audio/mpeg",
                filename=os.path.basename(default_file)
            )
        else:
            logger.error(f"No default audio available for the voice '{request.voice}'.")
            raise HTTPException(status_code=404, detail=f"No default audio available for the voice '{request.voice}'.")

    try:
        audio_stream = EL_CLIENT.text_to_speech.stream(
            text=request.text,
            voice_id=get_voice_id(request.voice),
            model_id=MODEL_ID,
        )
        logger.info("Stream function.")
        #stream(audio_stream)
        def audio_chunk_generator():
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    yield chunk

        logger.info("Streaming TTS audio back to frontend.")
        return StreamingResponse(
            audio_chunk_generator(),
            media_type="audio/mpeg",
            headers={"Accept-Ranges": "bytes"}
        )

    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")


def get_voice_id(voice_name: str) -> Optional[str]:
    return VOICE_MAPPING.get(voice_name.lower())


async def handle_generate_ws_audio(websocket: WebSocket):
    logger.info("WebSocket connecting.")
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        text, voice_name = validate_input(data, websocket)
        if not text or not voice_name:
            logger.error("Need to provide text and voice for processing.")
            raise HTTPException(status_code=422, detail="Please provide text and voice.")

        voice_id = get_voice_id(voice_name=voice_name)
        url, headers = construct_eleven_labs_ws_config(voice_id)

        await process_eleven_labs_connection(websocket, url, headers, text)

    except WebSocketDisconnect:
        logger.error("Client closed connection")
        print("Client closed connection")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        await websocket.close()


def validate_input(data: dict, websocket: WebSocket):
    text = data.get("text", "")
    voice_name = data.get("voice".lower(), "")

    if not text or not voice_name:
        websocket.close(code=4000)
        return None, None
    return text, voice_name


def construct_eleven_labs_ws_config(voice_id: str):
    url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"
    headers = [
        ("xi-api-key", get_eleven_labs_api_key()),
        ("accept", "application/json"),
    ]
    return url, headers


async def process_eleven_labs_connection(websocket: WebSocket, url: str, headers: list, text: str):
    async with websockets.connect(url, extra_headers=headers) as eleven_ws:

        await eleven_ws.send(json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.7
            },
            # "flush": True,
            "generation_config": {
                "output_format": "opus_48000_32",
                "auto_mode": True
            }
        }))
        # send empty text to mark the end of input
        await eleven_ws.send(json.dumps({
            "text": ""
        }))

        await stream_audio(websocket, eleven_ws)


async def stream_audio(websocket: WebSocket, eleven_ws):
    logger.info("WebSocket start stream audio.")
    while True:
        msg = await eleven_ws.recv()

        if isinstance(msg, str):
            obj = json.loads(msg)

            audio_b64 = obj.get("audio")
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_bytes(audio_bytes)

            if obj.get("isFinal") is True:
                break