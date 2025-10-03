import io
import os
import tempfile
import torch
import torchaudio as ta
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# --- Model and Device Setup ---

# Automatically select the best available device (CUDA, MPS, or CPU)
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"Using device: {device}")

# Load the multilingual TTS model from Hugging Face
try:
    tts_model = ChatterboxMultilingualTTS.from_pretrained(device=device)
except Exception as e:
    print(f"Error loading model: {e}")
    # Exit if the model can't be loaded, as the app is useless without it.
    exit()

# --- FastAPI Application ---

app = FastAPI()

# --- API Endpoints ---

@app.post("/tts")
async def generate_tts(
    text: str = Form(...),
    language: str = Form("en"),
    reference_audio: UploadFile = File(None),  # Reference audio is now optional
):
    """
    A single endpoint for both standard TTS and voice cloning.
    - If only text and language are provided, it performs standard TTS.
    - If reference_audio is also uploaded, it performs voice cloning.
    """
    audio_prompt_path = None
    temp_file_handle = None

    try:
        # If a reference audio file is provided, save it to a temporary file
        if reference_audio:
            # Create a temporary file to avoid race conditions
            temp_file_handle, audio_prompt_path = tempfile.mkstemp(suffix=".wav")
            with open(audio_prompt_path, "wb") as f:
                f.write(await reference_audio.read())

        # Generate TTS audio. If audio_prompt_path is None, it's standard TTS.
        # Otherwise, it's voice cloning.
        wav_out = tts_model.generate(
            text,
            language_id=language,
            audio_prompt_path=audio_prompt_path
        )

        # Save the generated audio into an in-memory buffer
        buffer = io.BytesIO()
        ta.save(buffer, wav_out, tts_model.sr, format="wav")
        buffer.seek(0)

        # Determine the correct filename for the output file
        output_filename = "voiceclone_output.wav" if reference_audio else "tts_output.wav"

        # Return the audio as a streaming response
        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )

    finally:
        # Cleanup: ensure the temporary file is deleted after the request is complete
        if audio_prompt_path and os.path.exists(audio_prompt_path):
            os.close(temp_file_handle)
            os.remove(audio_prompt_path)