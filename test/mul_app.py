import io
import torchaudio as ta
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# Load the model (GPU if available)
multilingual_model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")

app = FastAPI()

@app.post("/tts")
async def generate_tts(
    text: str = Form(...),
    language: str = Form("en"),
    reference_audio: UploadFile = File(None)
):
    # Optional: process reference audio if you actually want to use it
    if reference_audio:
        data = await reference_audio.read()
        wav, sr = ta.load(io.BytesIO(data))
        # hook here if Chatterbox ever adds voice adaptation

    # Generate TTS audio
    wav_out = multilingual_model.generate(text, language_id=language)

    # Save into in-memory buffer
    buffer = io.BytesIO()
    ta.save(buffer, wav_out, multilingual_model.sr, format="wav")
    buffer.seek(0)

    # Return as a streaming wav file
    return StreamingResponse(
        buffer,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=tts_output.wav"}
    )
