# Chatterbox Multilingual TTS + Voice Cloning Server

This project provides a **cloud-hosted TTS server** using Hugging Face’s **Chatterbox** models, deployed on **Lightning AI**. It supports:

1.  **Multilingual text-to-speech (TTS)** — generate speech from text in over 20 languages.
2.  **Voice cloning via reference audio** — synthesize text in the voice of a provided `.wav` file.

The project has been refactored to use a single, unified server endpoint and a flexible command-line client.

---

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Requirements](#requirements)
3.  [Lightning AI Setup](#lightning-ai-setup)
4.  [Server Endpoint](#server-endpoint)
5.  [Client Usage](#client-usage)
6.  [Curl Examples](#curl-examples)

---

## Project Overview

The server (`app.py`) runs on **FastAPI** and uses Hugging Face's `ChatterboxMultilingualTTS` model. It exposes a single public HTTPS endpoint on **Lightning AI** that intelligently handles both standard TTS and voice cloning based on the provided inputs.

Clients can send POST requests with either:

* `text` + `language` → Standard TTS
* `text` + `language` + `reference_audio` → Voice Cloning

The server returns a direct audio stream, which is saved as a `.wav` file.

---

## Requirements

* Python <=3.10
* Libraries (install via `pip install -r requirements.txt`):
    * `fastapi`
    * `uvicorn`
    * `torch`
    * `torchaudio`
    * `chatterbox-tts`
    * `requests`
* A Lightning AI account for cloud hosting.

---

## Lightning AI Setup

1.  **Install the Lightning CLI:**
    ```bash
    pip install lightning
    ```

2.  **Log in to your account:**
    ```bash
    lightning login
    ```

3.  **Run the server:**
    ```bash
    lightning run app app.py
    ```
    Lightning will provide you with a **public HTTPS URL** for your API. This is the URL you will use with the client.

---

## Server Endpoint

### Unified TTS and Voice Cloning

**POST** `/tts`

This single endpoint handles both functions.

**Form Data Parameters:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `text` | string | **Yes** | The text to be synthesized. |
| `language` | string | No | The language code (defaults to "en"). |
| `reference_audio`| file (.wav) | No | A `.wav` file for voice cloning. If provided, the output will mimic this voice. |

**Returns:**

* A WAV audio stream (`tts_output.wav` or `voiceclone_output.wav`).

---

## Client Usage (`client.py`)

The new `client.py` is a command-line tool. The first argument must be the server URL provided by Lightning AI.

### Standard TTS Example

```bash
python client.py "https://<your-lightning-url>/tts" \
    --text "Hello world, this is a standard text-to-speech example." \
    --lang "en" \
    --output "tts_example.wav"
```

### Voice Cloning Example

You need a reference audio file (e.g., `my_voice.wav`) for this.

```bash
python client.py "https://<your-lightning-url>/tts" \
    --text "This text will be spoken in the voice from the reference audio." \
    --ref_audio "my_voice.wav" \
    --lang "en" \
    --output "cloned_example.wav"
```

---

## Curl Examples

You can also interact with the API directly using `curl`.

### TTS with `curl`

```bash
curl -X POST "https://<your-lightning-url>/tts" \
     -F "text=Bonjour le monde" \
     -F "language=fr" \
     --output tts_output.wav
```

### Voice Cloning with `curl`

```bash
curl -X POST "https://<your-lightning-url>/tts" \
     -F "text=Hello, this is a cloned voice." \
     -F "language=en" \
     -F "reference_audio=@my_voice.wav" \
     --output cloned_output.wav
```