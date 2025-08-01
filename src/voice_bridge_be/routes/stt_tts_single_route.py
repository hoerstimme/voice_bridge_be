import asyncio
import base64
import json
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends, APIRouter
import aiohttp
import websockets
from starlette.websockets import WebSocketState

from voice_bridge_be import logger
from voice_bridge_be.common import get_rev_ai_key
from voice_bridge_be.routes.speech_to_text_rev_ai import extract_text_from_elements
from voice_bridge_be.services.text_to_speach_el import get_voice_id, construct_eleven_labs_ws_config, stream_audio

app = APIRouter()


@app.websocket("/ws/voice_bridge")
async def voice_bridge_endpoint(
    websocket: WebSocket,
    voice_name: str = Query("karl"),
    rev_ai_token: str = Depends(get_rev_ai_key)
):
    await websocket.accept()

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            f"wss://api.rev.ai/speechtotext/v1/stream"
            f"?access_token={rev_ai_token}"
            f"&content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1&language=de"
        ) as rev_ai_ws:

            await asyncio.gather(
                forward_audio_to_rev_ai(websocket, rev_ai_ws),
                handle_revai_and_forward_to_tts(websocket, rev_ai_ws, voice_name)
            )


async def forward_audio_to_rev_ai(websocket: WebSocket, rev_ai_ws: aiohttp.ClientWebSocketResponse):
    try:
        while True:
            chunk = await websocket.receive_bytes()
            logger.info(f"Received audio chunk size: {len(chunk)} bytes")
            await rev_ai_ws.send_bytes(chunk)
    except WebSocketDisconnect:
        logger.error("Client disconnected, sending EOS to Rev.ai")
        await rev_ai_ws.send_str("EOS")


async def handle_revai_and_forward_to_tts(websocket: WebSocket,
                                          rev_ai_ws: aiohttp.ClientWebSocketResponse,
                                          voice_name: str):
    last_partial = ""
    debounce_task = None
    flush_task = None

    # Helper: cancel tasks safely
    def cancel_task(task):
        if task and not task.done():
            task.cancel()

    async def debounce_send_tts(text):
        try:
            await asyncio.sleep(0.5)  # debounce 500ms
            # Pošalji na TTS
            await trigger_tts_and_stream(websocket, text, voice_name)
        except asyncio.CancelledError:
            # task je otkazan jer je došao novi partial pre isteka 500ms
            pass

    async def flush_send_tts(text):
        try:
            await asyncio.sleep(2)  # flush timeout 2s
            # Pošalji šta je zadnje stiglo na TTS
            await trigger_tts_and_stream(websocket, text, voice_name)
        except asyncio.CancelledError:
            pass

    try:
        async for msg in rev_ai_ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue

            data = json.loads(msg.data)
            msg_type = data.get("type")
            elements = data.get("elements", [])
            text = extract_text_from_elements(elements)

            if not text:
                continue

            if msg_type == "partial":
                # Pošalji partial na FE odmah
                if text != last_partial:
                    last_partial = text
                    await websocket.send_json({"type": "partial", "text": text})

                    # Resetuj debounce i flush taskove
                    cancel_task(debounce_task)
                    cancel_task(flush_task)

                    # Pokreni nove
                    debounce_task = asyncio.create_task(debounce_send_tts(text))
                    flush_task = asyncio.create_task(flush_send_tts(text))

            elif msg_type == "final":
                # Pošalji final samo FE
                await websocket.send_json({"type": "final", "text": text})
                last_partial = ""

                # Otkazi pending debounce/flush taskove jer final je stigao
                cancel_task(debounce_task)
                cancel_task(flush_task)

    except Exception as e:
        logger.error("Error in STT-TTS handling:", e)


async def trigger_tts_and_stream(websocket: WebSocket, text: str, voice_name: str):
    voice_id = get_voice_id(voice_name)
    url, headers = construct_eleven_labs_ws_config(voice_id)

    try:
        async with websockets.connect(url, extra_headers=headers) as eleven_ws:
            await eleven_ws.send(json.dumps({
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.7
                },
                "generation_config": {
                    "output_format": "opus_48000_32",
                    "auto_mode": True
                }
            }))
            await eleven_ws.send(json.dumps({"text": ""}))

            await stream_audio(websocket, eleven_ws)

    except Exception as e:
        logger.error("TTS stream error:", e)