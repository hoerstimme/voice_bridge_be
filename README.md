# 🎙 Voice Bridge Backend (FastAPI)

This branch contains the **backend implementation** for multiple speech transformation options, including:

- **STS with ElevenLabs (Speech-to-Speech)** – compatible with the frontend implementation from [voice_bridge_fe](https://github.com/hoerstimme/voice_bridge_fe).
- **RevAI + ElevenLabs** (STT + TTS, bidirectional WebSocket).
- Other experimental features (described in the code and comments).

---

⚠ **Note:**  
If you are using the above-mentioned frontend, use **only** the STS with ElevenLabs route, and route for getting available voices:  
`/convert_voice_stream_bytes_webm`
`/available_voices`

---

## 📋 Prerequisites

Make sure you have the following installed:

- **Python 3.12+**
- **Poetry** (for dependency management)
- **ElevenLabs API key** (to be stored in `.env`)

---

## ⚙️ `.env` Configuration

In the backend root directory, create a `.env` file with the following content:

```env
DB_HOST=value
DB_PORT=value
POSTGRES_USER=value
POSTGRES_PASSWORD=value
POSTGRES_DB=value
OPENAI_API_KEY=your_openai_api_key_here
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key_here
ELEVEN_LABS_URL=https://api.elevenlabs.io/v1/text-to-speech/
GEMINI_API_KEY_DEV=your_gemini_api_key_here
REV_AI_API_KEY_DEV=your_revai_api_key_here
```

This feature relies solely on ELEVEN_LABS_API_KEY. However, due to the overall project configuration, all other environment variables must also be included in the .env file, even if they are not used in this particular feature.

---

# 🛠 Installation & Run

1️⃣ Clone the repository (or checkout this branch):
```bash
git clone https://github.com/hoerstimme/voice_bridge_be.git
cd voice_bridge_be
git checkout branch_name (ex. feat/voice_to_voice)
```

2️⃣ Install Poetry (if you don’t have it yet):
```bash
pip install poetry
```

3️⃣ Install dependencies:
```bash
poetry install
```

4️⃣ Start the server:
```bash
poetry run uvicorn voice_bridge_be.main:app --host 127.0.0.1 --port 8001 --log-level debug
```

The server will be available at:

http://127.0.0.1:8001

---

# 📡 Relevant Endpoint for Frontend (STS with ElevenLabs)

POST /convert_voice_stream_bytes_webm

- Receives an audio chunk from the frontend (WebM format) and the voice_name parameter.
- Processes the chunk using the ElevenLabs STS API.
- Returns an audio file ready for playback.

---

# 🧪 Other Features in This Branch

In addition to STS with ElevenLabs, this branch also includes:

- RevAI STT integration
- RevAI + ElevenLabs combination
- Examples of asynchronous WebSocket STT-TTS streaming


## 🪪 License

The software is released under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/),  
which permits noncommercial use, modification, and distribution.

That means:

- ✅ You can **view, clone, and modify** the code for **personal, academic, or research use**.
- 🚫 You **cannot use, sell, or integrate** this code in **commercial applications**.
- 🧠 You must **include this license** in any copies or derivatives.

For commercial or partnership inquiries, please contact:  
📧 ps@sinceare.com

See the full license text at:  
🔗 [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)

## 🏢 Ownership

All code and related assets in this repository are the intellectual property of  
**sinceare UG (haftungsbeschränkt)**, Berlin, Germany.