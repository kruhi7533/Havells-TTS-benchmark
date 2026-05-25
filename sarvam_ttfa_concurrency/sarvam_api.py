import os
import time
import json
import base64
import asyncio
import websockets

MODEL = "bulbul:v3"
WS_URL = f"wss://api.sarvam.ai/text-to-speech/ws?model={MODEL}&send_completion_event=true"

# Language name → Sarvam language code mapping
LANGUAGE_CODES = {
    "english":   "en-IN",
    "hindi":     "hi-IN",
    "bengali":   "bn-IN",
    "gujarati":  "gu-IN",
    "kannada":   "kn-IN",
    "malayalam": "ml-IN",
    "tamil":     "ta-IN",
    "telugu":    "te-IN",
}


async def generate_tts_async(text, language, output_path=None):

    api_key = os.getenv("SARVAM_API_KEY")

    headers = {
        "Api-Subscription-Key": api_key
    }

    first_chunk_time = None
    audio_chunks = []

    try:
        async with websockets.connect(
            WS_URL,
            additional_headers=headers
        ) as ws:

            # CONFIG
            lang_code = LANGUAGE_CODES.get(language.lower(), "hi-IN")
            await ws.send(json.dumps({
                "type": "config",
                "data": {
                    "target_language_code": lang_code,
                    "speaker": "priya"
                }
            }))

            # START TIMER
            start_time = time.perf_counter()

            # TEXT
            await ws.send(json.dumps({
                "type": "text",
                "data": {"text": text}
            }))

            await ws.send(json.dumps({"type": "flush"}))

            async for response in ws:

                now = time.perf_counter()

                message = json.loads(response)
                msg_type = message.get("type")

                # ✅ CORRECT AUDIO DETECTION
                if msg_type == "audio":

                    if first_chunk_time is None:
                        first_chunk_time = now

                    audio_base64 = message["data"]["audio"]
                    audio_chunks.append(base64.b64decode(audio_base64))

                elif msg_type == "event":
                    if message.get("data", {}).get("event_type") == "final":
                        break

                elif msg_type == "completion":
                    break

                elif msg_type == "error":
                    return False, None, None, message

        if first_chunk_time is None:
            return False, None, None, "No audio detected"

        ttfa = first_chunk_time - start_time

        if output_path and audio_chunks:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"".join(audio_chunks))

        return True, ttfa, None, "Success"

    except Exception as e:
        return False, None, None, str(e)