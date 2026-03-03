import os
import pandas as pd
import subprocess

ELEVEN_FOLDER = "../outputs/propernouns/elevenlabs"
SARVAM_FOLDER = "../outputs/propernouns/sarvam"
OUTPUT_CSV = "../logs/propernoun_manual_ratings.csv"

# =========================
# LOAD EXISTING RATINGS (RESUME SUPPORT)
# =========================
if os.path.exists(OUTPUT_CSV):
    df_existing = pd.read_csv(OUTPUT_CSV)
    rated_phrases = set(df_existing["phrase"].tolist())
    results = df_existing.to_dict("records")
    print(f"Resuming... {len(rated_phrases)} already rated.")
else:
    rated_phrases = set()
    results = []

# =========================
# SORT FILES NUMERICALLY
# =========================
files = sorted(
    os.listdir(ELEVEN_FOLDER),
    key=lambda x: int(os.path.splitext(x)[0].split("_")[-1])
)

total = len(files)
counter = 0

for file in files:
    phrase = os.path.splitext(file)[0]

    if phrase in rated_phrases:
        continue  # Skip already rated

    counter += 1
    print(f"\n===== {counter}/{total} =====")
    print(f"Phrase: {phrase}")

    eleven_path = os.path.join(ELEVEN_FOLDER, file)

    sarvam_mp3 = os.path.join(SARVAM_FOLDER, phrase + ".mp3")
    sarvam_wav = os.path.join(SARVAM_FOLDER, phrase + ".wav")

    if os.path.exists(sarvam_mp3):
        sarvam_path = sarvam_mp3
    elif os.path.exists(sarvam_wav):
        sarvam_path = sarvam_wav
    else:
        print(f"Sarvam audio not found for {phrase}")
        continue

    print("Playing Eleven...")
    subprocess.run(["start", eleven_path], shell=True)
    input("Press Enter to continue...")

    print("Playing Sarvam...")
    subprocess.run(["start", sarvam_path], shell=True)
    input("Press Enter to continue...")

    # =========================
    # VALIDATE INPUT
    # =========================
    while True:
        try:
            eleven_score = int(input("Rate Eleven (1-3): "))
            if eleven_score in [1,2,3]:
                break
        except:
            pass
        print("Invalid input. Enter 1, 2, or 3.")

    while True:
        try:
            sarvam_score = int(input("Rate Sarvam (1-3): "))
            if sarvam_score in [1,2,3]:
                break
        except:
            pass
        print("Invalid input. Enter 1, 2, or 3.")

    if eleven_score > sarvam_score:
        better = "ElevenLabs"
    elif sarvam_score > eleven_score:
        better = "Sarvam"
    else:
        better = "Tie"

    results.append({
        "phrase": phrase,
        "eleven_score": eleven_score,
        "sarvam_score": sarvam_score,
        "better_model": better
    })

    # =========================
    # AUTO SAVE AFTER EACH ENTRY
    # =========================
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print("Saved.")

print("\nAll phrases rated successfully.")