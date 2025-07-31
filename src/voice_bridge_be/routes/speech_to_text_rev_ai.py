import asyncio
import aiohttp
from aiohttp import ClientWebSocketResponse
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from voice_bridge_be.common import get_rev_ai_key

app = APIRouter()


async def handle_revai_responses(websocket: WebSocket,
                                 revai_ws: ClientWebSocketResponse):
    try:
        async for msg in revai_ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await process_revai_text_message(msg, websocket)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("Rev.ai WebSocket error:", msg)
                break
    except Exception as e:
        print("Error receiving from Rev.ai:", e)

last_partial_text = ""

async def process_revai_text_message(msg, websocket):
    global last_partial_text

    data = json.loads(msg.data)
    msg_type = data.get("type", "unknown")

    elements = data.get("elements", [])
    text = extract_text_from_elements(elements)

    if not text:
        return

    if msg_type == "partial":
        if text != last_partial_text:
            last_partial_text = text

            await websocket.send_json({
                "type": "partial",
                "text": text
            })
    elif msg_type == "final":

        await websocket.send_json({
            "type": "final",
            "text": text
        })
        last_partial_text = ""


def extract_text_from_elements(elements):
    return ' '.join([
        el["value"] for el in elements
        if el["type"] in ("text", "punct")
    ]).strip()


async def forward_audio(websocket: WebSocket,
                        revai_ws: ClientWebSocketResponse):
    try:
        while True:
            chunk = await websocket.receive_bytes()
            print(f"Received audio chunk size: {len(chunk)} bytes")
            await revai_ws.send_bytes(chunk)
    except WebSocketDisconnect:
        print("FE closed WebSocket, sending EOS")
        await revai_ws.send_str("EOS")


@app.websocket("/ws/stt/transcribe")
async def websocket_transcribe(websocket: WebSocket, token: str = Depends(get_rev_ai_key)):
    await websocket.accept()

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            f"wss://api.rev.ai/speechtotext/v1/stream"
            f"?access_token={token}"
            f"&content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1&language=de"
        ) as revai_ws:

            await asyncio.gather(
                forward_audio(websocket=websocket, revai_ws=revai_ws),
                handle_revai_responses(websocket=websocket, revai_ws=revai_ws)
            )
