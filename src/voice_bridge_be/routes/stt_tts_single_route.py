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


import asyncio
import json


from fastapi import WebSocket, Query, Depends, APIRouter
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
    voice_name: str = Query("Ben"),
    rev_ai_token: str = Depends(get_rev_ai_key)
):
    await websocket.accept()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                f"wss://api.rev.ai/speechtotext/v1/stream"
                f"?access_token={rev_ai_token}"
                f"&content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1"
                f"&language=de"
            ) as rev_ai_ws:

                logger.info("✅ WebSocket connections established: client <-> Rev.ai")

                # Define the two main coroutines
                forward_task = asyncio.create_task(
                    forward_audio_to_rev_ai(websocket, rev_ai_ws)
                )

                tts_task = asyncio.create_task(
                    handle_revai_and_forward_to_tts(websocket, rev_ai_ws, voice_name)
                )

                # Wait for both tasks to finish or be cancelled
                await asyncio.gather(forward_task, tts_task)

    except Exception as e:
        logger.exception(f"❌ Error in /ws/voice_bridge endpoint: {e}")


async def forward_audio_to_rev_ai(websocket: WebSocket, rev_ai_ws: aiohttp.ClientWebSocketResponse):
    try:
        while True:
            message = await websocket.receive()
            print(message)
            if message["type"] == "websocket.disconnect":
                logger.warning("🔌 WebSocket client disconnected unexpectedly")
                if not rev_ai_ws.closed:
                    await rev_ai_ws.send_str("EOS")
                break

            elif "bytes" in message:
                chunk = message["bytes"]

                if rev_ai_ws.closed:
                    logger.warning("🚫 Rev.ai WebSocket is already closed, cannot send audio.")
                    break

                logger.info(f"🎧 Received audio chunk size: {len(chunk)} bytes")
                await rev_ai_ws.send_bytes(chunk)

            elif "text" in message and message["text"] == "EOS":
                logger.info("📨 Received EOS from client — closing Rev.ai connection")
                await rev_ai_ws.send_str("EOS")
                break

    except Exception as e:
        logger.exception(f"❌ Exception while forwarding audio to Rev.ai: {e}")


async def handle_revai_and_forward_to_tts(websocket: WebSocket,
                                          rev_ai_ws: aiohttp.ClientWebSocketResponse,
                                          voice_name: str):
    try:
        async for msg in rev_ai_ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                msg_type = data.get("type")
                elements = data.get("elements", [])
                text = extract_text_from_elements(elements)

                if not text:
                    continue

                if msg_type == "partial":
                    logger.info(f"📤 Sending partial to FE: {text}")
                    await websocket.send_json({"type": "partial", "text": text})

                elif msg_type == "final":
                    logger.info(f"📤 Sending final to FE: {text}")
                    await websocket.send_json({"type": "final", "text": text})

                    logger.info(f"🗣️ Sending final to TTS: {text}")
                    await trigger_tts_and_stream(websocket, text, voice_name)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"❌ Rev.ai WebSocket error: {rev_ai_ws.exception()}")
                break

            elif msg.type == aiohttp.WSMsgType.CLOSE:
                logger.warning(f"🔌 Rev.ai WebSocket closed. Code: {rev_ai_ws.close_code}")
                break

    except Exception as e:
        logger.exception("❌ Error in STT-TTS handling:", exc_info=e)


async def trigger_tts_and_stream(websocket: WebSocket, text: str, voice_name: str):
    voice_id = get_voice_id(voice_name)
    if not voice_id:
        logger.error(f"❌ Invalid voice ID for voice '{voice_name}'")
        return

    url, headers = construct_eleven_labs_ws_config(voice_id)

    try:
        logger.info(f"🔁 Forwarding text to ElevenLabs: '{text}' with voice '{voice_name}'")
        logger.info(f"🌐 Connecting to ElevenLabs WS at: {url}")

        async with websockets.connect(url, extra_headers=headers) as eleven_ws:
            logger.info("🟢 WebSocket connection to Eleven Labs established.")

            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "language_code": "de",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.7
                },
                "generation_config": {
                    "output_format": "opus_48000_32"
                }
            }
            logger.info(f"📤 Payload to Eleven Labs:\n{json.dumps(payload, indent=2)}")

            await eleven_ws.send(json.dumps(payload))
            await eleven_ws.send(json.dumps({"text": ""}))

            await stream_audio(websocket, eleven_ws)

    except asyncio.CancelledError:
        logger.warning("TTS task cancelled")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()

    except Exception as e:
        logger.exception(f"❌ Error during Eleven Labs WS connection: {e}")
