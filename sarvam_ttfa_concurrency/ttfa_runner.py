import asyncio
import csv
import os

from sarvam_api import generate_tts_async, LANGUAGE_CODES

# Always run relative to this file's location
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =========================
# CONFIG
# =========================
LANGUAGES = list(LANGUAGE_CODES.keys())  # all 8 languages
MAX_SENTENCES = 100

LOG_PATH = "logs/ttfa_raw.csv"
os.makedirs("logs", exist_ok=True)


# =========================
# LOAD DATASET
# =========================
def load_dataset(language):
    path = f"dataset/{language}.txt"

    # handle capitalized filenames
    if not os.path.exists(path):
        path = f"dataset/{language.capitalize()}.txt"

    if not os.path.exists(path):
        print(f"Dataset missing: {language}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()][:MAX_SENTENCES]


# =========================
# MAIN RUNNER
# =========================
async def run():

    # ✅ Validate API key before starting
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        print("❌ ERROR: SARVAM_API_KEY environment variable is not set!")
        print("   Run: $env:SARVAM_API_KEY = 'your-key-here'  (PowerShell)")
        return
    print(f"✅ API key found: {api_key[:8]}...")

    print("Warmup...")
    warmup = await generate_tts_async("Hello", "english")
    if not warmup[0]:
        print(f"⚠️  Warmup FAILED: {warmup[3]}")
        print("   Check your API key and network connection.")
        return
    print(f"✅ Warmup OK — TTFA: {warmup[1]*1000:.1f} ms")

    file_exists = os.path.isfile(LOG_PATH)

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "language",
                "text",
                "ttfa_ms",
                "status"
            ])

        # =========================
        # LOOP THROUGH LANGUAGES
        # =========================
        for lang in LANGUAGES:

            dataset = load_dataset(lang)

            if not dataset:
                continue

            print(f"\nLanguage: {lang}")

            success_count = 0
            total_ttfa = 0

            for i, text in enumerate(dataset):

                # retry once (important for stability)
                for _ in range(2):
                    result = await generate_tts_async(text, lang)
                    if result[0]:
                        break

                success, ttfa, total, msg = result

                # convert safely
                ttfa_ms = ttfa * 1000 if ttfa else 0

                writer.writerow([
                    lang,
                    text,
                    round(ttfa_ms, 2),
                    msg
                ])

                if success:
                    success_count += 1
                    total_ttfa += ttfa_ms

                # reduce logging noise
                if (i + 1) % 10 == 0:
                    avg = total_ttfa / success_count if success_count else 0
                    print(f"{i+1}/{len(dataset)} | Avg TTFA: {avg:.2f} ms")

            final_avg = total_ttfa / success_count if success_count else 0
            print(f"Final Avg TTFA ({lang}): {final_avg:.2f} ms")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    asyncio.run(run())