# Chatterbox Multilingual TTS + Voice Cloning Server

This project provides a **cloud-hosted TTS server** using Hugging Face’s **Chatterbox** models, deployed on **Lightning AI**. It supports:

1.  **Multilingual text-to-speech (TTS)** — generate speech from text in over 20 languages.
2.  **Voice cloning via reference audio** — synthesize text in the voice of a provided `.wav` file.
3.  **Real-time streaming** — process long texts in chunks for faster response times.

The project includes both regular HTTP endpoints and WebSocket streaming for optimal performance with different use cases.

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

## Server Endpoints

### Regular TTS and Voice Cloning

**POST** `/tts`

This endpoint handles both standard TTS and voice cloning.

**Form Data Parameters:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `text` | string | **Yes** | The text to be synthesized. |
| `language` | string | No | The language code (defaults to "en"). |
| `reference_audio`| file (.wav) | No | A `.wav` file for voice cloning. If provided, the output will mimic this voice. |

**Returns:**

* A WAV audio stream (`tts_output.wav` or `voiceclone_output.wav`).

### Streaming TTS (WebSocket)

**WebSocket** `/tts-stream`

This endpoint provides real-time streaming TTS generation for faster response times.

**WebSocket Message Format:**

```json
{
  "text": "Your text to synthesize",
  "language": "en",
  "reference_audio": "base64_encoded_wav_data"  // optional
}
```

**Response Format:**

The server sends multiple JSON messages:

1. **Info Message:**
```json
{
  "type": "info",
  "total_chunks": 5,
  "message": "Processing 5 chunks..."
}
```

2. **Audio Chunk Messages:**
```json
{
  "type": "audio_chunk",
  "chunk_index": 0,
  "total_chunks": 5,
  "audio_data": "base64_encoded_wav_data",
  "text_chunk": "First sentence of text.",
  "is_final": false
}
```

3. **Error Messages:**
```json
{
  "type": "error",
  "error": "Error description"
}
```

**Benefits of Streaming:**
- Faster perceived response time
- Real-time processing feedback
- Better handling of long texts
- Reduced memory usage for large texts

---

## Client Usage

### Regular Client (`client.py`)

The `client.py` is a command-line tool that supports both regular and streaming modes. The first argument must be the server URL provided by Lightning AI.

#### Standard TTS Example

```bash
python client.py "https://<your-lightning-url>/tts" \
    --text "Hello world, this is a standard text-to-speech example." \
    --lang "en" \
    --output "tts_example.wav"
```

#### Voice Cloning Example

You need a reference audio file (e.g., `my_voice.wav`) for this.

```bash
python client.py "https://<your-lightning-url>/tts" \
    --text "This text will be spoken in the voice from the reference audio." \
    --ref_audio "my_voice.wav" \
    --lang "en" \
    --output "cloned_example.wav"
```

#### Streaming Mode (Faster Response)

Add the `--stream` flag to use streaming mode, which breaks text into chunks and processes them in real-time:

```bash
python client.py "https://<your-lightning-url>/tts" \
    --text "This is a long text that will be processed in chunks for faster streaming response. Each sentence will be processed separately and streamed back as soon as it's ready." \
    --lang "en" \
    --output "streaming_example.wav" \
    --stream
```

### Dedicated Streaming Client (`streaming_client.py`)

The dedicated streaming client provides **real-time audio playback** - you hear the audio as it's generated!

#### With Real-time Playback (Recommended)
```bash
python streaming_client.py "https://<your-lightning-url>/tts" \
    --text "Your long text here..." \
    --lang "en" \
    --output "streaming_output.wav"
```

#### Without Real-time Playback (Save Only)
```bash
python streaming_client.py "https://<your-lightning-url>/tts" \
    --text "Your long text here..." \
    --lang "en" \
    --output "streaming_output.wav" \
    --no-play
```

#### Features:
- 🎵 **Real-time playback**: Hear audio chunks as they're generated
- 📁 **Automatic saving**: Combined audio saved to file after playback
- 🔄 **Synchronous queue**: Chunks play in order, waiting for next chunk if needed
- 🎛️ **Fallback support**: Works with or without audio libraries

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

---

## Testing Streaming Functionality

Use the provided test script to verify streaming works:

```bash
python test_streaming.py
```

Remember to update the `server_url` in the test script with your actual Lightning AI URL.

---

## Performance Comparison

| Mode | Best For | Response Time | Memory Usage |
|------|----------|---------------|--------------|
| **Regular** | Short texts (<200 chars) | Full processing time | Lower server memory |
| **Streaming** | Long texts (>200 chars) | First chunk in ~2-3s | Higher server memory |

---

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure your Lightning AI deployment supports WebSocket connections
   - Check that the URL is correct (should start with `wss://` for HTTPS deployments)

2. **Streaming Client Not Found**
   - Make sure `streaming_client.py` is in the same directory as `client.py`
   - Install required dependencies: `pip install websockets`

3. **Audio Quality Issues**
   - For voice cloning, ensure reference audio is clear and at least 3-5 seconds long
   - Use WAV format for reference audio (16kHz or 22kHz recommended)

4. **Large Text Processing**
   - Streaming automatically chunks text at sentence boundaries
   - Maximum chunk size is 200 characters (configurable in server code)
   - Very long texts may take time to process all chunks

### Performance Tips

- Use streaming mode for texts longer than 200 characters
- For voice cloning, provide high-quality reference audio
- Consider using shorter sentences for better chunk boundaries
- Monitor server logs for processing times and errors

### Connection Issues Debugging

If you're experiencing connection drops or "unknown format" errors:

1. **Test the connection first:**
   ```bash
   python test_connection.py "https://your-lightning-url/tts"
   ```

2. **Install client dependencies:**
   ```bash
   pip install -r client_requirements.txt
   ```
   
   For real-time audio playback, install one of these:
   ```bash
   pip install pygame          # Recommended - easier to install
   # OR
   pip install pyaudio         # Alternative - may need system dependencies
   ```

3. **Check for audio format issues:**
   - The error "unknown format: 3" indicates WAV file combination problems
   - The updated client uses torchaudio for better audio handling
   - If issues persist, individual chunk files will be saved as fallback

4. **Lightning AI specific considerations:**
   - Ensure your deployment supports WebSocket connections
   - Check that the server isn't timing out during processing
   - Monitor server logs for memory or processing issues

5. **Network stability:**
   - Use a stable internet connection
   - Consider reducing chunk size for unstable connections
   - The client includes automatic reconnection handling