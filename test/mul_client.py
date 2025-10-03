import requests

API_URL = "https://7860-01k6maprxpehcykhskfne1wyer.cloudspaces.litng.ai/tts"

def text_to_speech(text, language="en", reference_audio=None, output_file="output.wav"):
    data = {"text": text, "language": language}
    files = {}

    if reference_audio:
        files["reference_audio"] = open(reference_audio, "rb")

    response = requests.post(API_URL, data=data, files=files)
    response.raise_for_status()

    with open(output_file, "wb") as f:
        f.write(response.content)

    print(f"Saved audio to {output_file}")

text_to_speech("This one includes reference audio.", "en", reference_audio="audio.wav", output_file="ref.wav")
