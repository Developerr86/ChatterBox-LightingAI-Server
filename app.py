import base64
import io
import torchaudio as ta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# Load the model on CUDA if available
multilingual_model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")

app = FastAPI()

@app.post("/tts")
async def generate_tts(request: Request):
    body = await request.json()
    text = body.get("text")
    language = body.get("language", "en")

    if not text:
        return JSONResponse(content={"error": "No text provided"}, status_code=400)

    # Generate audio
    wav = multilingual_model.generate(text, language_id=language)

    # Save to memory buffer as WAV
    buffer = io.BytesIO()
    ta.save(buffer, wav, multilingual_model.sr, format="wav")
    buffer.seek(0)

    # Encode as base64
    audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return JSONResponse(content={"audio": audio_base64})
