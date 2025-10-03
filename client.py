import base64
import requests

API_URL = "https://7860-01k6maprxpehcykhskfne1wyer.cloudspaces.litng.ai/tts"

def text_to_speech(text, language="en", output_file="output.wav"):
    payload = {"text": text, "language": language}
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()

    audio_base64 = response.json()["audio"]

    with open(output_file, "wb") as f:
        f.write(base64.b64decode(audio_base64))

    print(f"Saved audio to {output_file}")

# Example usage
text_to_speech("The old librarian, a man named Elias Vance, adjusted his spectacles and peered at the peculiar contraption whirring softly on his mahogany desk. It was a gift from a traveling inventor, a small, intricate sphere of brass and polished obsidian that purportedly cataloged dreams. According to the inventor's questionable instructions, one simply had to place it by their bedside before sleeping.", "en", "english.wav")
