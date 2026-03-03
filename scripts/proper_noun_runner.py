import os
import csv
from elevenlabs_api import generate_elevenlabs_audio
from sarvam_api import generate_sarvam_audio

# =========================
# CONFIG
# =========================

VOICE_ID = "vYENaCJHl4vFKNDYPr8y"
DATASET_PATH = "../dataset/proper_noun.txt"

OUTPUT_BASE = "../outputs/propernouns"
LOG_FILE = "../logs/propernoun_latency.csv"

# =========================
# LOAD DATASET
# =========================

def load_proper_nouns():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# =========================
# CREATE FOLDERS
# =========================

os.makedirs(f"{OUTPUT_BASE}/elevenlabs", exist_ok=True)
os.makedirs(f"{OUTPUT_BASE}/sarvam", exist_ok=True)
os.makedirs("../logs", exist_ok=True)

# =========================
# RUN TEST
# =========================

proper_nouns = load_proper_nouns()

with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "phrase",
        "model",
        "latency_ms",
        "status",
        "output_file"
    ])

    for i, phrase in enumerate(proper_nouns):

        # ElevenLabs
        eleven_output = f"{OUTPUT_BASE}/elevenlabs/proper_{i+1}.mp3"
        success, latency, message = generate_elevenlabs_audio(
            phrase,
            VOICE_ID,
            eleven_output
        )

        writer.writerow([
            phrase,
            "ElevenLabs",
            round(latency * 1000, 2),
            "Success" if success else message,
            eleven_output
        ])

        # Sarvam
        sarvam_output = f"{OUTPUT_BASE}/sarvam/proper_{i+1}.wav"
        success, latency, message = generate_sarvam_audio(
            phrase,
            sarvam_output
        )

        writer.writerow([
            phrase,
            "Sarvam",
            round(latency * 1000, 2),
            "Success" if success else message,
            sarvam_output
        ])

print("Proper noun generation completed.")