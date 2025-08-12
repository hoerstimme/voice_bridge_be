# 🎙 Voice Bridge Backend (FastAPI)

This branch contains the **backend implementation** for multiple speech transformation options, including:

- **STS with ElevenLabs (Speech-to-Speech)** – compatible with the frontend implementation from [voice_bridge_fe](https://github.com/hoerstimme/voice_bridge_fe).
- **RevAI + ElevenLabs** (STT + TTS, bidirectional WebSocket).
- Other experimental features (described in the code and comments).

---

⚠ **Note:**  
If you are using the above-mentioned frontend, use **only** the STS with ElevenLabs route:  
`/convert_voice_stream_bytes_webm`

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
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key_here
```

---

# 🛠 Installation & Run

1️⃣ Clone the repository (or checkout this branch):

git clone https://github.com/hoerstimme/voice_bridge_be.git
cd voice_bridge_be
git checkout branch_name (ex. feat/voice_to_voice)

2️⃣ Install Poetry (if you don’t have it yet):

pip install poetry

3️⃣ Install dependencies:

poetry install

4️⃣ Start the server:

poetry run uvicorn voice_bridge_be.main:app --host 127.0.0.1 --port 8001 --log-level debug

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
