import requests

API_URL = "https://7860-01k6maprxpehcykhskfne1wyer.cloudspaces.litng.ai"

def text_to_speech(text, language="en", output_file="tts.wav"):
    data = {"text": text, "language": language}
    response = requests.post(f"{API_URL}/tts", data=data)
    response.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(response.content)
    print(f"[TTS] Saved to {output_file}")

def voice_clone(text, reference_audio, language="en", output_file="cloned.wav"):
    data = {"text": text, "language": language}
    files = {"reference_audio": open(reference_audio, "rb")}
    response = requests.post(f"{API_URL}/voiceclone", data=data, files=files)
    response.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(response.content)
    print(f"[VoiceClone] Saved to {output_file}")

# Example usage:
text_to_speech("Hello world", "en", "plain.wav")
voice_clone("Hello, this is cloned speech.", "audio.wav", "en", "cloned.wav")
