import os
import requests
import time

def generate_elevenlabs_audio(text, voice_id, output_path):
    api_key = os.getenv("ELEVENLABS_API_KEY")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    latency = time.time() - start_time

    if response.status_code != 200:
        return False, latency, response.text

    if output_path:
        with open(output_path, "wb") as f:
            f.write(response.content)

    return True, latency, "Success"