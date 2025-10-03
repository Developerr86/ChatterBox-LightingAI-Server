# Chatterbox Multilingual TTS + Voice Cloning Server

This project provides a **cloud-hosted TTS server** using Hugging Face’s **Chatterbox** models, deployed on **Lightning AI**. It supports:

1. **Multilingual text-to-speech (TTS)** — generate speech from text in 23+ languages.
2. **Voice cloning via reference audio** — synthesize text in the voice of a reference `.wav` file.

The project includes:

* A **server** (`app.py`) running **FastAPI**, exposing clean endpoints for TTS and voice cloning.
* A **client** (`client.py`) for sending text and optional reference audio to the server, saving the resulting `.wav`.
* `curl` examples for testing without Python.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Requirements](#requirements)
3. [Lightning AI Setup](#lightning-ai-setup)
4. [Server Endpoints](#server-endpoints)
5. [Client Usage](#client-usage)
6. [Curl Examples](#curl-examples)
7. [Voice Cloning Details](#voice-cloning-details)
8. [Notes and Tips](#notes-and-tips)

---

## Project Overview

The server uses Hugging Face **Chatterbox** models:

* **`ChatterboxMultilingualTTS`** — converts text → speech, supports 23+ languages.
* **`ChatterboxVC` (optional)** — can do full voice conversion (though in this project, we use reference audio TTS).

The server is designed to run on **Lightning AI** with API Builder, exposing public HTTPS endpoints. Clients can send POST requests with either:

* `text` + `language` → TTS
* `text` + `language` + `reference_audio` → TTS mimicking the reference voice

Audio is returned directly as a `.wav` file (no base64 encoding needed).

---

## Requirements

* Python <=3.10
* Libraries (via `requirements.txt`):

```
fastapi
uvicorn
torch
torchaudio
chatterbox-tts
```

* Lightning AI account (for cloud hosting)

Optional for local GPU acceleration: CUDA or MPS.

---

## Lightning AI Setup

1. Install Lightning CLI:

```bash
pip install lightning
```

2. Log in:

```bash
lightning login
```

3. Structure your project:

```
chatterbox_server/
├── app.py
├── client.py
├── requirements.txt
└── lightning_app.py   # Optional wrapper for Lightning API Builder
```

4. Run the server:

```bash
lightning run app app.py
```

5. Lightning will provide a **public HTTPS URL** for your API.

---

## Server Endpoints

### 1. Multilingual TTS

**POST** `/tts`

**Form Data Parameters:**

| Parameter | Type   | Required | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| text      | string | yes      | Text to synthesize            |
| language  | string | no       | Language code (default: "en") |

**Returns:**

* WAV audio stream (`tts_output.wav`)

---

### 2. Voice Cloning via Reference Audio

**POST** `/voiceclone`

**Form Data Parameters:**

| Parameter       | Type        | Required | Description                   |
| --------------- | ----------- | -------- | ----------------------------- |
| text            | string      | yes      | Text to synthesize            |
| language        | string      | no       | Language code (default: "en") |
| reference_audio | file (.wav) | yes      | Reference audio for cloning   |

**Returns:**

* WAV audio stream (`voiceclone_output.wav`)

**Note:** The `reference_audio` is used as an audio prompt to guide the TTS output voice.

---

## Client Usage (`client.py`)

```python
from client import text_to_speech, voice_clone

# Plain TTS
text_to_speech("Hello world", "en", "tts.wav")

# TTS with reference voice
voice_clone("This is cloned speech.", "reference.wav", "en", "cloned.wav")
```

---

## Curl Examples

### TTS

```bash
curl -X POST "https://<your-lightning-url>/tts" \
     -F "text=Bonjour le monde" \
     -F "language=fr" \
     --output tts_output.wav
```

### Voice Cloning with Reference Audio

```bash
curl -X POST "https://<your-lightning-url>/voiceclone" \
     -F "text=Hello, this is cloned speech." \
     -F "language=en" \
     -F "reference_audio=@reference.wav" \
     --output cloned_output.wav
```

---

## Voice Cloning Details

* Voice cloning is implemented using **Chatterbox TTS with audio prompt** (`audio_prompt_path`).
* This approach allows you to synthesize text in the style of a speaker from a single `.wav` file.
* No separate source speech file is required — just provide the text and a reference `.wav`.

---

## Notes and Tips

* **Optional GPU:** CUDA or MPS will speed up inference; otherwise, CPU works but slower.
* **Temporary files:** Server saves uploaded reference audio temporarily; these could be removed if desired.
* **Lightning free tier:** May spin down the server if idle; consider a paid plan for continuous availability.
* **Extending functionality:** You can merge `/tts` and `/voiceclone` into a single endpoint by making `reference_audio` optional.

---

This setup gives you a **full-featured multilingual TTS API with voice cloning** that’s easy to call from Python, `curl`, or any HTTP client.

---

If you want, I can also **add a small architecture diagram and example workflow** section to this README, showing how the client → Lightning API → Chatterbox flow works visually. That makes it even easier for new users to understand.
