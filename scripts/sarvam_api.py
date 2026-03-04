import os
import requests
import base64
import time

def generate_sarvam_audio(text, output_path):
    api_key = os.getenv("SARVAM_API_KEY")

    url = "https://api.sarvam.ai/text-to-speech"

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "target_language_code": "hi-IN",
        "model": "bulbul:v3",
        "speaker": "priya"
    }

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    latency = time.time() - start_time

    if response.status_code != 200:
        return False, latency, response.text

    response_json = response.json()
    audio_base64 = response_json["audios"][0]
    audio_bytes = base64.b64decode(audio_base64)

    if output_path:
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

    return True, latency, "Success"