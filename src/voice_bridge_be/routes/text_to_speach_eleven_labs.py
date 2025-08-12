from fastapi import APIRouter, Depends
from starlette import status
from starlette.websockets import WebSocket

from voice_bridge_be.common import get_eleven_labs_api_key
from voice_bridge_be.database.request_models import AudioRequest
from voice_bridge_be.database.response_models import AvailableVoices
from voice_bridge_be.services.text_to_speach_el import VOICE_MAPPING, produce_stream_audio, handle_generate_ws_audio

app = APIRouter()


@app.get("/available_voices",
         status_code=status.HTTP_200_OK,
         response_model=AvailableVoices)
def list_voices():
    return AvailableVoices(voices=[voice_name.capitalize() for voice_name in VOICE_MAPPING.keys()])


@app.post("/tts/stream_audio",
          status_code=status.HTTP_201_CREATED)
# response_model=)
def generate_stream_audio(request: AudioRequest,
                          eleven_labs_key: str = Depends(get_eleven_labs_api_key)
                          ):
    return produce_stream_audio(request=request)


@app.websocket("/ws/tts/generate_audio")
async def generate_ws_audio(websocket: WebSocket):
    await handle_generate_ws_audio(websocket)
