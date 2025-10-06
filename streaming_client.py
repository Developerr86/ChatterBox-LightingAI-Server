import asyncio
import websockets
import json
import base64
import argparse
import wave
import io
import threading
import queue
import time
from pathlib import Path

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available - install with: pip install pygame")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("pyaudio not available - install with: pip install pyaudio")

class AudioPlayer:
    """Handles real-time audio playback using pygame or pyaudio."""
    
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.playing = False
        self.player_thread = None
        self.audio_chunks_data = []  # Store for saving later
        self.chunks_played = 0
        self.total_chunks = 0
        self.playback_finished = threading.Event()
        
        # Initialize audio system
        if PYGAME_AVAILABLE:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
            self.use_pygame = True
            print("Using pygame for audio playback")
        elif PYAUDIO_AVAILABLE:
            self.use_pygame = False
            self.pyaudio = pyaudio.PyAudio()
            print("Using pyaudio for audio playback")
        else:
            raise Exception("No audio library available. Install pygame or pyaudio.")
    
    def start_playback(self):
        """Start the audio playback thread."""
        if not self.playing:
            self.playing = True
            self.player_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.player_thread.start()
    
    def stop_playback(self):
        """Stop audio playback."""
        self.playing = False
        if self.player_thread:
            self.player_thread.join(timeout=2)
    
    def set_total_chunks(self, total):
        """Set the expected total number of chunks."""
        self.total_chunks = total
        self.chunks_played = 0
        self.playback_finished.clear()
    
    def add_chunk(self, audio_data_b64):
        """Add an audio chunk to the playback queue."""
        try:
            audio_data = base64.b64decode(audio_data_b64)
            self.audio_chunks_data.append(audio_data)  # Store for saving
            self.audio_queue.put(audio_data)
        except Exception as e:
            print(f"Error adding audio chunk: {e}")
    
    def wait_for_completion(self, timeout=30):
        """Wait for all audio chunks to finish playing."""
        return self.playback_finished.wait(timeout)
    
    def _playback_worker(self):
        """Worker thread for audio playback."""
        if self.use_pygame:
            self._pygame_playback()
        else:
            self._pyaudio_playback()
    
    def _pygame_playback(self):
        """Playback using pygame."""
        while self.playing:
            try:
                # Wait for audio chunk with timeout
                audio_data = self.audio_queue.get(timeout=1)
                
                # Create temporary file for pygame
                temp_file = io.BytesIO(audio_data)
                
                # Load and play the audio
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    if not self.playing:
                        pygame.mixer.music.stop()
                        break
                
                # Track completion
                self.chunks_played += 1
                print(f"🎵 Finished playing chunk {self.chunks_played}/{self.total_chunks}")
                
                # Check if all chunks are done
                if self.chunks_played >= self.total_chunks and self.total_chunks > 0:
                    print("🎉 All audio chunks have finished playing!")
                    self.playback_finished.set()
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                # Check if we're done but no more chunks coming
                if self.chunks_played >= self.total_chunks and self.total_chunks > 0:
                    self.playback_finished.set()
                continue
            except Exception as e:
                print(f"Pygame playback error: {e}")
    
    def _pyaudio_playback(self):
        """Playback using pyaudio."""
        stream = None
        try:
            while self.playing:
                try:
                    # Wait for audio chunk
                    audio_data = self.audio_queue.get(timeout=1)
                    
                    # Read WAV file to get parameters
                    wav_io = io.BytesIO(audio_data)
                    with wave.open(wav_io, 'rb') as wav_file:
                        frames = wav_file.readframes(wav_file.getnframes())
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        sample_width = wav_file.getsampwidth()
                    
                    # Create stream if not exists or parameters changed
                    if stream is None:
                        stream = self.pyaudio.open(
                            format=self.pyaudio.get_format_from_width(sample_width),
                            channels=channels,
                            rate=sample_rate,
                            output=True
                        )
                    
                    # Play the audio
                    stream.write(frames)
                    
                    # Track completion
                    self.chunks_played += 1
                    print(f"🎵 Finished playing chunk {self.chunks_played}/{self.total_chunks}")
                    
                    # Check if all chunks are done
                    if self.chunks_played >= self.total_chunks and self.total_chunks > 0:
                        print("🎉 All audio chunks have finished playing!")
                        self.playback_finished.set()
                    
                    self.audio_queue.task_done()
                    
                except queue.Empty:
                    # Check if we're done but no more chunks coming
                    if self.chunks_played >= self.total_chunks and self.total_chunks > 0:
                        self.playback_finished.set()
                    continue
                except Exception as e:
                    print(f"PyAudio playback error: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
    
    def save_combined_audio(self, output_file):
        """Save all received chunks as a combined WAV file."""
        if not self.audio_chunks_data:
            print("No audio chunks to save")
            return
        
        try:
            # Simple approach: concatenate raw audio data
            all_frames = b""
            params = None
            
            for i, chunk_data in enumerate(self.audio_chunks_data):
                try:
                    chunk_io = io.BytesIO(chunk_data)
                    with wave.open(chunk_io, 'rb') as chunk_wav:
                        if params is None:
                            params = chunk_wav.getparams()
                        
                        # Read all frames from this chunk
                        frames = chunk_wav.readframes(chunk_wav.getnframes())
                        all_frames += frames
                        
                except Exception as e:
                    print(f"Warning: Could not process chunk {i}: {e}")
                    continue
            
            if params and all_frames:
                # Write combined audio
                with wave.open(output_file, 'wb') as output_wav:
                    output_wav.setparams(params)
                    output_wav.writeframes(all_frames)
                
                print(f"Successfully saved combined audio to '{output_file}'")
                return
            
        except Exception as e:
            print(f"Error saving combined audio: {e}")
        
        # Fallback: save individual chunks
        print("Falling back to individual chunk files...")
        for i, chunk_data in enumerate(self.audio_chunks_data):
            try:
                filename = f"chunk_{i:03d}.wav"
                with open(filename, "wb") as f:
                    f.write(chunk_data)
                print(f"Saved {filename}")
            except Exception as chunk_error:
                print(f"Error saving chunk {i}: {chunk_error}")
    
    def cleanup(self):
        """Cleanup audio resources."""
        self.stop_playback()
        if not self.use_pygame and hasattr(self, 'pyaudio'):
            self.pyaudio.terminate()

class StreamingTTSClient:
    def __init__(self, server_url, enable_playback=True):
        # Convert HTTP URL to WebSocket URL
        if server_url.startswith("https://"):
            self.ws_url = server_url.replace("https://", "wss://").replace("/tts", "/tts-stream")
        elif server_url.startswith("http://"):
            self.ws_url = server_url.replace("http://", "ws://").replace("/tts", "/tts-stream")
        else:
            # Assume it's already a WebSocket URL
            self.ws_url = server_url
        
        self.enable_playback = enable_playback
        self.audio_player = None
        
        if self.enable_playback:
            try:
                self.audio_player = AudioPlayer()
            except Exception as e:
                print(f"Audio playback disabled: {e}")
                self.enable_playback = False
        
    def encode_audio_file(self, file_path):
        """Encode audio file to base64."""
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"Error: Reference audio file not found at '{file_path}'")
            return None
    
    async def stream_tts(self, text, language="en", reference_audio=None, output_file="streaming_output.wav", play_audio=True):
        """Stream TTS generation with real-time playback and save the result."""
        reference_audio_b64 = None
        
        if reference_audio:
            reference_audio_b64 = self.encode_audio_file(reference_audio)
            if reference_audio_b64 is None:
                return
        
        # Start audio playback if enabled
        if self.enable_playback and play_audio and self.audio_player:
            self.audio_player.start_playback()
            print("🔊 Real-time audio playback enabled")
        
        try:
            print(f"Connecting to: {self.ws_url}")
            async with websockets.connect(self.ws_url) as websocket:
                # Send request
                request = {
                    "text": text,
                    "language": language
                }
                
                if reference_audio_b64:
                    request["reference_audio"] = reference_audio_b64
                
                await websocket.send(json.dumps(request))
                print("Request sent, waiting for response...")
                
                total_chunks = 0
                chunks_received = 0
                
                # Receive responses
                async for message in websocket:
                    try:
                        response = json.loads(message)
                        
                        if response.get("type") == "info":
                            total_chunks = response.get("total_chunks", 0)
                            print(f"Server: {response.get('message', '')}")
                            # Set total chunks for playback tracking
                            if self.audio_player and play_audio:
                                self.audio_player.set_total_chunks(total_chunks)
                        
                        elif response.get("type") == "audio_chunk":
                            chunk_index = response.get("chunk_index", 0)
                            audio_data = response.get("audio_data", "")
                            text_chunk = response.get("text_chunk", "")
                            is_final = response.get("is_final", False)
                            
                            chunks_received += 1
                            print(f"🎵 Playing chunk {chunks_received}/{total_chunks}: '{text_chunk[:50]}{'...' if len(text_chunk) > 50 else ''}'")
                            
                            # Add to playback queue immediately
                            if self.audio_player and play_audio:
                                self.audio_player.add_chunk(audio_data)
                            
                            if is_final:
                                print("✅ All chunks received and queued for playback!")
                                break
                        
                        elif response.get("type") == "error":
                            print(f"❌ Server error: {response.get('error', 'Unknown error')}")
                            return
                        
                        else:
                            print(f"Unknown response type: {response}")
                    
                    except json.JSONDecodeError:
                        print(f"Failed to parse server response: {message}")
                
                # Wait for playback to finish and save combined audio
                if self.audio_player:
                    if play_audio and total_chunks > 0:
                        print("⏳ Waiting for all audio chunks to finish playing...")
                        # Wait for all chunks to complete playback
                        playback_completed = await asyncio.get_event_loop().run_in_executor(
                            None, self.audio_player.wait_for_completion, 30
                        )
                        
                        if playback_completed:
                            print("🎉 All audio playback completed!")
                        else:
                            print("⚠️  Playback timeout - proceeding to save...")
                        
                        # Give a small buffer for any remaining audio
                        await asyncio.sleep(0.5)
                    
                    # Save combined audio file
                    print(f"💾 Saving combined audio to {output_file}...")
                    self.audio_player.save_combined_audio(output_file)
                
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            # Cleanup
            if self.audio_player:
                self.audio_player.cleanup()

def main():
    parser = argparse.ArgumentParser(description="Streaming client for Chatterbox TTS with real-time playback")
    
    parser.add_argument("server_url", help="Server URL (e.g., https://<your-lightning-url>/tts)")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--lang", default="en", help="Language code")
    parser.add_argument("--ref_audio", help="Path to reference audio file for voice cloning")
    parser.add_argument("--output", default="streaming_output.wav", help="Output audio file")
    parser.add_argument("--no-play", action="store_true", help="Disable real-time audio playback")
    
    args = parser.parse_args()
    
    # Check audio libraries
    if not args.no_play and not (PYGAME_AVAILABLE or PYAUDIO_AVAILABLE):
        print("⚠️  No audio playback libraries available.")
        print("Install with: pip install pygame  OR  pip install pyaudio")
        print("Continuing without real-time playback...")
        args.no_play = True
    
    client = StreamingTTSClient(args.server_url, enable_playback=not args.no_play)
    
    # Run the streaming client
    asyncio.run(client.stream_tts(
        text=args.text,
        language=args.lang,
        reference_audio=args.ref_audio,
        output_file=args.output,
        play_audio=not args.no_play
    ))

if __name__ == "__main__":
    main()