import os
import pandas as pd
import wave
import json
from mutagen.mp3 import MP3
from datetime import datetime

# Rates (INR per character)
COST_SARVAM = 0.0015
COST_ELEVENLABS = 0.004

# Model/Voice constants
MODEL_ELEVEN = "eleven_multilingual_v2"
VOICE_ELEVEN = "vYENaCJHl4vFKNDYPr8y"
MODEL_SARVAM = "bulbul:v3"
VOICE_SARVAM = "priya"

RAW_LOG_PATH = "../logs/latency_raw.csv"
OUTPUT_EXCEL = "../outputs/detailed_benchmark_report.xlsx"

def get_wav_info(file_path):
    try:
        with wave.open(file_path, "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            # Bitrate = SampleRate * BitsPerSample * Channels
            # wave doesn't directly give bits per sample easily without more calls, 
            # but usually it's 16-bit for these APIs. 
            # Bitrate (bps) = (size_bytes * 8) / duration
            size = os.path.getsize(file_path)
            bitrate = (size * 8) / duration if duration > 0 else 0
            return duration, rate, bitrate
    except Exception as e:
        print(f"Error reading WAV {file_path}: {e}")
        return 0, 0, 0

def get_mp3_info(file_path):
    try:
        audio = MP3(file_path)
        duration = audio.info.length
        sample_rate = audio.info.sample_rate
        bitrate = audio.info.bitrate
        return duration, sample_rate, bitrate
    except Exception as e:
        print(f"Error reading MP3 {file_path}: {e}")
        return 0, 0, 0

def analyze():
    if not os.path.exists(RAW_LOG_PATH):
        print(f"Log file {RAW_LOG_PATH} not found.")
        return

    df = pd.read_csv(RAW_LOG_PATH)
    
    # Filter only success rows
    df = df[df['status'] == 'Success'].copy()
    
    analyzed_data = []

    for i, row in df.iterrows():
        text = str(row['text'])
        model = row['model']
        latency_sec = row['latency_seconds']
        output_file = row['output_file']
        
        # Absolute path for processing
        # benchmark_runner uses ../outputs, so from root it's outputs/
       # Convert relative path to absolute safely
        abs_output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), output_file)) 
        
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
        
        # Throughput = chars / (total_latency in seconds)
        throughput = char_count / (total_latency_ms / 1000) if total_latency_ms > 0 else 0
        
        cost = char_count * (COST_ELEVENLABS if model == "ElevenLabs" else COST_SARVAM)
        
        model_name = MODEL_ELEVEN if model == "ElevenLabs" else MODEL_SARVAM
        voice = VOICE_ELEVEN if model == "ElevenLabs" else VOICE_SARVAM
        
        analyzed_data.append({
            "run_id": i + 1,
            "timestamp": row['timestamp'],
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
            "bitrate": round(bitrate / 1000, 2) if bitrate > 0 else 0, # in kbps
            "estimated_cost": round(cost, 4)
        })

    results_df = pd.DataFrame(analyzed_data)
    
    os.makedirs(os.path.dirname(OUTPUT_EXCEL), exist_ok=True)
    with pd.ExcelWriter(OUTPUT_EXCEL, engine="xlsxwriter") as writer:
        results_df.to_excel(writer, sheet_name="Full Analysis", index=False)
        
        # Professional formatting
        workbook = writer.book
        worksheet = writer.sheets["Full Analysis"]
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        for col_num, value in enumerate(results_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)

    print(f"Analysis complete. Report saved to {OUTPUT_EXCEL}")

if __name__ == "__main__":
    analyze()