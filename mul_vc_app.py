import io
import torch
import torchaudio as ta
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# Pick device automatically
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

# Load multilingual TTS model
tts_model = ChatterboxMultilingualTTS.from_pretrained(device=device)

app = FastAPI()

# -------------------------------
# 1. Regular multilingual TTS
# -------------------------------
@app.post("/tts")
async def generate_tts(
    text: str = Form(...),
    language: str = Form("en"),
):
    wav_out = tts_model.generate(text, language_id=language)

    buffer = io.BytesIO()
    ta.save(buffer, wav_out, tts_model.sr, format="wav")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=tts_output.wav"}
    )


# -------------------------------
# 2. Voice Cloning (TTS with reference audio prompt)
# -------------------------------
@app.post("/voiceclone")
async def voice_clone(
    text: str = Form(...),
    language: str = Form("en"),
    reference_audio: UploadFile = File(...),  # the audio prompt for cloning
):
    # Save reference audio temporarily
    ref_path = "temp_prompt.wav"
    with open(ref_path, "wb") as f:
        f.write(await reference_audio.read())

    # Generate TTS in reference voice
    wav_out = tts_model.generate(
        text,
        language_id=language,
        audio_prompt_path=ref_path
    )

    buffer = io.BytesIO()
    ta.save(buffer, wav_out, tts_model.sr, format="wav")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=voiceclone_output.wav"}
    )
