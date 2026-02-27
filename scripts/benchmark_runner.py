import os
import csv
import datetime
import json
from elevenlabs_api import generate_elevenlabs_audio
from sarvam_api import generate_sarvam_audio

# Set working directory to script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

VOICE_ID = "vYENaCJHl4vFKNDYPr8y"

# =========================
# LANGUAGE CONFIG
# =========================
LANGUAGES = [
    "english",
    "hindi",
    "tamil",
    "bengali",
    "kannada",
    "telugu",
    "malayalam",
    "gujarati"
]

MAX_SENTENCES = 50

LOG_DIR = "../logs"
LOG_PATH = os.path.join(LOG_DIR, "latency_raw.csv")
PROGRESS_FILE = "../logs/progress.json"

os.makedirs(LOG_DIR, exist_ok=True)

# Ensure API Keys exist
if not os.getenv("ELEVENLABS_API_KEY"):
    print("WARNING: ELEVENLABS_API_KEY not found.")
if not os.getenv("SARVAM_API_KEY"):
    print("WARNING: SARVAM_API_KEY not found.")


def run_benchmark():

    # =========================
    # LOAD PROGRESS
    # =========================
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as pf:
            try:
                progress_data = json.load(pf)
            except:
                progress_data = {}
    else:
        progress_data = {}

    # =========================
    # LOOP THROUGH LANGUAGES
    # =========================
    for LANGUAGE in LANGUAGES:

        print("\n===============================")
        print(f"Running language: {LANGUAGE}")
        print("===============================")

        DATASET_PATH = f"../dataset/{LANGUAGE}.txt"
        OUTPUT_DIR_ELEVEN = f"../outputs/elevenlabs/{LANGUAGE}"
        OUTPUT_DIR_SARVAM = f"../outputs/sarvam/{LANGUAGE}"

        os.makedirs(OUTPUT_DIR_ELEVEN, exist_ok=True)
        os.makedirs(OUTPUT_DIR_SARVAM, exist_ok=True)

        if not os.path.exists(DATASET_PATH):
            print(f"{DATASET_PATH} not found. Skipping.")
            continue

        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Limit to 25 sentences per run
        lines = lines[:MAX_SENTENCES]

        dataset_name = os.path.basename(DATASET_PATH)
        start_index = progress_data.get(dataset_name, 0)

        print(f"Starting from index: {start_index}")

        file_exists = os.path.isfile(LOG_PATH)

        with open(LOG_PATH, "a", newline="", encoding="utf-8") as log_file:
            writer = csv.writer(log_file)

            if not file_exists:
                writer.writerow([
                    "timestamp",
                    "language",
                    "text",
                    "model",
                    "latency_seconds",
                    "status",
                    "output_file"
                ])

            for i, text in enumerate(lines[start_index:], start=start_index):

                text = text.strip()
                if not text:
                    continue

                timestamp = datetime.datetime.now()

                print(f"Processing index {i}")

                # =========================
                # ELEVENLABS
                # =========================
                eleven_path = f"{OUTPUT_DIR_ELEVEN}/{LANGUAGE}_{i}.mp3"
                success, latency, message = generate_elevenlabs_audio(
                    text, VOICE_ID, eleven_path
                )

                writer.writerow([
                    timestamp,
                    LANGUAGE,
                    text,
                    "ElevenLabs",
                    latency,
                    message,
                    eleven_path
                ])

                # =========================
                # SARVAM
                # =========================
                sarvam_path = f"{OUTPUT_DIR_SARVAM}/{LANGUAGE}_{i}.wav"
                success, latency, message = generate_sarvam_audio(
                    text,
                    sarvam_path
                )

                writer.writerow([
                    timestamp,
                    LANGUAGE,
                    text,
                    "Sarvam",
                    latency,
                    message,
                    sarvam_path
                ])

                # =========================
                # UPDATE PROGRESS
                # =========================
                progress_data[dataset_name] = i + 1

                with open(PROGRESS_FILE, "w") as pf:
                    json.dump(progress_data, pf, indent=4)

        print(f"Completed batch for {LANGUAGE}")


if __name__ == "__main__":
    run_benchmark()