import io
import os
import tempfile
import torch
import torchaudio as ta
import json
import re
import base64
from fastapi import FastAPI, Form, File, UploadFile, WebSocket, WebSocketDisconnect
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

# --- Helper Functions ---

def chunk_text(text, max_chunk_size=200):
    """
    Split text into chunks at sentence boundaries, respecting max_chunk_size.
    """
    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed max size, save current chunk
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

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

@app.websocket("/tts-stream")
async def tts_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming TTS generation.
    Client sends: {"text": "...", "language": "en", "reference_audio": "base64_encoded_wav_data"}
    Server responds with chunks: {"chunk_index": 0, "audio_data": "base64_encoded_wav", "is_final": false}
    """
    await websocket.accept()
    audio_prompt_path = None
    temp_file_handle = None
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            text = request_data.get("text", "")
            language = request_data.get("language", "en")
            reference_audio_b64 = request_data.get("reference_audio")
            
            if not text:
                await websocket.send_text(json.dumps({
                    "error": "Text is required"
                }))
                continue
            
            # Handle reference audio if provided
            if reference_audio_b64:
                try:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(reference_audio_b64)
                    temp_file_handle, audio_prompt_path = tempfile.mkstemp(suffix=".wav")
                    with open(audio_prompt_path, "wb") as f:
                        f.write(audio_data)
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "error": f"Failed to process reference audio: {str(e)}"
                    }))
                    continue
            
            # Split text into chunks
            text_chunks = chunk_text(text)
            total_chunks = len(text_chunks)
            
            # Send total chunks info
            await websocket.send_text(json.dumps({
                "type": "info",
                "total_chunks": total_chunks,
                "message": f"Processing {total_chunks} chunks..."
            }))
            
            # Process each chunk
            for i, chunk in enumerate(text_chunks):
                try:
                    # Check if connection is still alive
                    if websocket.client_state.name != "CONNECTED":
                        print(f"Client disconnected during chunk {i}")
                        break
                    
                    # Generate TTS for this chunk
                    wav_out = tts_model.generate(
                        chunk,
                        language_id=language,
                        audio_prompt_path=audio_prompt_path
                    )
                    
                    # Convert audio to base64 with better error handling
                    buffer = io.BytesIO()
                    try:
                        ta.save(buffer, wav_out, tts_model.sr, format="wav")
                        buffer.seek(0)
                        audio_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    except Exception as audio_error:
                        print(f"Audio encoding error for chunk {i}: {audio_error}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "chunk_index": i,
                            "error": f"Audio encoding failed: {str(audio_error)}"
                        }))
                        continue
                    
                    # Send chunk to client with connection check
                    response = {
                        "type": "audio_chunk",
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                        "audio_data": audio_b64,
                        "text_chunk": chunk,
                        "is_final": i == total_chunks - 1
                    }
                    
                    try:
                        await websocket.send_text(json.dumps(response))
                        print(f"Sent chunk {i+1}/{total_chunks} to client")
                    except Exception as send_error:
                        print(f"Failed to send chunk {i}: {send_error}")
                        break
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "chunk_index": i,
                        "error": f"Failed to process chunk {i}: {str(e)}"
                    }))
            
            # Cleanup reference audio file after processing
            if audio_prompt_path and os.path.exists(audio_prompt_path):
                os.close(temp_file_handle)
                os.remove(audio_prompt_path)
                audio_prompt_path = None
                temp_file_handle = None
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e)
            }))
        except:
            pass
    finally:
        # Final cleanup
        if audio_prompt_path and os.path.exists(audio_prompt_path):
            try:
                os.close(temp_file_handle)
                os.remove(audio_prompt_path)
            except:
                pass