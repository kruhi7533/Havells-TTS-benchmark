import os
import csv
import datetime
import json
from elevenlabs_api import generate_elevenlabs_audio
from sarvam_api import generate_sarvam_audio

VOICE_ID = "vYENaCJHl4vFKNDYPr8y"
LANGUAGE = "english"

DATASET_PATH = f"../dataset/{LANGUAGE}.txt"
OUTPUT_DIR_ELEVEN = "../outputs/elevenlabs"
OUTPUT_DIR_SARVAM = "../outputs/sarvam"
LOG_PATH = "../logs/latency_raw.csv"

os.makedirs(OUTPUT_DIR_ELEVEN, exist_ok=True)
os.makedirs(OUTPUT_DIR_SARVAM, exist_ok=True)
os.makedirs("../logs", exist_ok=True)


def run_benchmark():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # =========================
    # PROGRESS TRACKING
    # =========================
    progress_file = "../logs/progress.json"
    dataset_name = os.path.basename(DATASET_PATH)

    if os.path.exists(progress_file):
        with open(progress_file, "r") as pf:
            try:
                progress_data = json.load(pf)
            except:
                progress_data = {}
    else:
        progress_data = {}

    start_index = progress_data.get(dataset_name, 0)

    print(f"\nStarting {dataset_name} from index {start_index}")

    file_exists = os.path.isfile(LOG_PATH)

    with open(LOG_PATH, "a", newline="") as log_file:
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

            print(f"\nProcessing: {text}")

            # ElevenLabs
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
            print("ElevenLabs latency:", round(latency, 3))

            # Sarvam
            sarvam_path = f"{OUTPUT_DIR_SARVAM}/{LANGUAGE}_{i}.wav"
            success, latency, message = generate_sarvam_audio(
                text, sarvam_path
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
            print("Sarvam latency:", round(latency, 3))

            # =========================
            # UPDATE PROGRESS
            # =========================
            progress_data[dataset_name] = i + 1

            with open(progress_file, "w") as pf:
                json.dump(progress_data, pf, indent=4)

if __name__ == "__main__":
    run_benchmark()