import os
import pandas as pd
import wave
from mutagen.mp3 import MP3

# =========================
# COST CONFIG
# =========================
COST_SARVAM = 0.0015
COST_ELEVENLABS = 0.004

MODEL_ELEVEN = "eleven_v3"
VOICE_ELEVEN = "vYENaCJHl4vFKNDYPr8y"

MODEL_SARVAM = "bulbul:v3"
VOICE_SARVAM = "priya"

# =========================
# FILE PATHS
# =========================
ENGLISH_LOG = "../logs/english_latency_raw.csv"
MULTI_LOG = "../logs/latency_raw_multilingual.csv"

ENGLISH_DETAIL_OUT = "../outputs/detailed_english.xlsx"
MULTI_DETAIL_OUT = "../outputs/detailed_multilingual.xlsx"

FINAL_REPORT = "tts_benchmark_report.xlsx"


# =========================
# AUDIO INFO HELPERS
# =========================
def get_wav_info(file_path):
    try:
        with wave.open(file_path, "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            size = os.path.getsize(file_path)
            bitrate = (size * 8) / duration if duration > 0 else 0
            return duration, rate, bitrate
    except:
        return 0, 0, 0


def get_mp3_info(file_path):
    try:
        audio = MP3(file_path)
        return audio.info.length, audio.info.sample_rate, audio.info.bitrate
    except:
        return 0, 0, 0


# =========================
# DETAILED ANALYZER FUNCTION
# =========================
def run_detailed_analysis(raw_log_path, output_excel_path):

    if not os.path.exists(raw_log_path):
        print(f"{raw_log_path} not found.")
        return pd.DataFrame()

    df = pd.read_csv(raw_log_path)
    df = df[df["status"] == "Success"].copy()

    analyzed_data = []

    for i, row in df.iterrows():

        text = str(row["text"])
        model = row["model"]
        latency_sec = row["latency_seconds"]
        output_file = row["output_file"]

        abs_output_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), output_file)
        )

        char_count = len(text)
        word_count = len(text.split())
        latency_ms = latency_sec * 1000

        audio_duration_sec = 0
        sample_rate = 0
        bitrate = 0
        audio_size_bytes = 0

        if os.path.exists(abs_output_path):
            audio_size_bytes = os.path.getsize(abs_output_path)

            if abs_output_path.endswith(".wav"):
                audio_duration_sec, sample_rate, bitrate = get_wav_info(abs_output_path)

            elif abs_output_path.endswith(".mp3"):
                audio_duration_sec, sample_rate, bitrate = get_mp3_info(abs_output_path)

        total_latency_ms = latency_ms + (audio_duration_sec * 1000)

        throughput = (
            char_count / (total_latency_ms / 1000)
            if total_latency_ms > 0 else 0
        )

        cost = char_count * (
            COST_ELEVENLABS if model == "ElevenLabs" else COST_SARVAM
        )

        model_name = MODEL_ELEVEN if model == "ElevenLabs" else MODEL_SARVAM
        voice = VOICE_ELEVEN if model == "ElevenLabs" else VOICE_SARVAM

        analyzed_data.append({
            "run_id": i + 1,
            "timestamp": row["timestamp"],
            "provider": model,
            "model_name": model_name,
            "voice": voice,
            "char_count": char_count,
            "word_count": word_count,
            "latency_ms": round(latency_ms, 2),
            "audio_duration_sec": round(audio_duration_sec, 3),
            "total_latency_ms": round(total_latency_ms, 2),
            "throughput_chars_per_sec": round(throughput, 2),
            "audio_size_bytes": audio_size_bytes,
            "sample_rate": sample_rate,
            "bitrate": round(bitrate / 1000, 2) if bitrate > 0 else 0,
            "estimated_cost": round(cost, 4)
        })

    results_df = pd.DataFrame(analyzed_data)

    os.makedirs(os.path.dirname(output_excel_path), exist_ok=True)

    with pd.ExcelWriter(output_excel_path, engine="xlsxwriter") as writer:
        results_df.to_excel(writer, sheet_name="Full Analysis", index=False)

    print(f"Detailed analysis saved to {output_excel_path}")
    return results_df


# =========================
# SEQUENTIAL SUMMARY
# =========================
def calculate_sequential_summary(df):

    df = df[df["status"] == "Success"].copy()
    summary_rows = []

    for model_name in df["model"].unique():

        model_df = df[df["model"] == model_name]
        latencies = model_df["latency_seconds"] * 1000

        if len(latencies) > 0:
            avg = latencies.mean()
            p95 = latencies.quantile(0.95)
            std = latencies.std()
            min_val = latencies.min()
            max_val = latencies.max()
            total_time = latencies.sum() / 1000
            throughput = len(latencies) / total_time if total_time > 0 else 0
        else:
            avg = p95 = std = min_val = max_val = throughput = 0

        summary_rows.append({
            "model": model_name,
            "avg_latency_ms": round(avg, 2),
            "p95_latency_ms": round(p95, 2),
            "std_dev_ms": round(std, 2),
            "min_latency_ms": round(min_val, 2),
            "max_latency_ms": round(max_val, 2),
            "throughput_req_per_sec": round(throughput, 2)
        })

    return pd.DataFrame(summary_rows)


# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":

    # Run detailed analysis
    english_detailed_df = run_detailed_analysis(
        ENGLISH_LOG, ENGLISH_DETAIL_OUT
    )

    multilingual_detailed_df = run_detailed_analysis(
        MULTI_LOG, MULTI_DETAIL_OUT
    )

    english_df = pd.read_csv(ENGLISH_LOG)
    multilingual_df = pd.read_csv(MULTI_LOG)

    english_summary_df = calculate_sequential_summary(english_df)

    # Optional concurrency
    try:
        concurrency_summary_df = pd.read_csv("../logs/concurrency_summary.csv")
    except:
        concurrency_summary_df = None

    # Final Excel
    with pd.ExcelWriter(FINAL_REPORT, engine="xlsxwriter") as writer:

        english_detailed_df.to_excel(writer, sheet_name="English Detailed", index=False)
        multilingual_detailed_df.to_excel(writer, sheet_name="Multilingual Detailed", index=False)

        english_df.to_excel(writer, sheet_name="English Raw", index=False)
        multilingual_df.to_excel(writer, sheet_name="Multilingual Raw", index=False)

        english_summary_df.to_excel(writer, sheet_name="Sequential Summary", index=False)

        if concurrency_summary_df is not None:
            concurrency_summary_df.to_excel(
                writer, sheet_name="Concurrency Summary", index=False
            )

    print("Final professional benchmark report created!")