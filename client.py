import argparse
import requests

def make_api_request(api_url, text, language, reference_audio=None, output_file="output.wav"):
    """
    Sends a request to the TTS server for either standard TTS or voice cloning.
    """
    print(f"Sending request to: {api_url}")

    # Prepare the form data
    data = {"text": text, "language": language}
    files = {}

    # If a reference audio file is provided, add it to the request
    if reference_audio:
        try:
            files["reference_audio"] = open(reference_audio, "rb")
        except FileNotFoundError:
            print(f"Error: Reference audio file not found at '{reference_audio}'")
            return

    try:
        # Send the POST request to the server
        response = requests.post(api_url, data=data, files=files)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Save the returned audio content to a file
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Successfully saved audio to '{output_file}'")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the file handle for the reference audio is closed
        if "reference_audio" in files and files["reference_audio"]:
            files["reference_audio"].close()

def main():
    """
    Main function to parse command-line arguments and trigger the API request.
    """
    parser = argparse.ArgumentParser(description="Client for the Chatterbox TTS and Voice Cloning API")

    # Define command-line arguments
    parser.add_argument("server_url", help="The full URL of the TTS server (e.g., https://<your-lightning-url>/tts)")
    parser.add_argument("--text", required=True, help="The text to synthesize")
    parser.add_argument("--lang", default="en", help="The language code (e.g., 'en', 'fr', 'es')")
    parser.add_argument("--ref_audio", help="Path to the reference .wav file for voice cloning (optional)")
    parser.add_argument("--output", default="output.wav", help="The filename for the output audio")

    args = parser.parse_args()

    # Call the function to make the API request
    make_api_request(args.server_url, args.text, args.lang, args.ref_audio, args.output)

if __name__ == "__main__":
    main()