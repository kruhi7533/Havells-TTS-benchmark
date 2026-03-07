import os
import pandas as pd
import wave
from mutagen.mp3 import MP3

# =========================
# COST CONFIG
# =========================
COST_SARVAM = 0.003
COST_ELEVENLABS = 0.0037

MODEL_ELEVEN = "eleven_v3"
VOICE_ELEVEN = "vYENaCJHl4vFKNDYPr8y"

MODEL_SARVAM = "bulbul:v3"
VOICE_SARVAM = "priya"

# =========================
# FILE PATHS
# =========================
PROPER_NOUN_LOG = "../logs/propernoun_latency.csv"
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
        language=row.get("language","")

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
            "language":language,
            "provider": model,
            "model_name": model_name,
            "voice": voice,
            "char_count": char_count,
            "word_count": word_count,
            "latency_ms": round(latency_ms, 2),
            "audio_duration_sec": round(audio_duration_sec, 3),
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
    # =========================
    # COST COMPARISON
    # =========================

    all_data = pd.concat([english_detailed_df, multilingual_detailed_df])

    cost_summary = all_data.groupby("provider")["estimated_cost"].sum()

    cost_eleven = cost_summary.get("ElevenLabs", 0)
    cost_sarvam = cost_summary.get("Sarvam", 0)

    cost_winner = "Sarvam" if cost_sarvam < cost_eleven else "ElevenLabs"

    print("ElevenLabs total cost:", cost_eleven)
    print("Sarvam total cost:", cost_sarvam)
    print("Cheaper provider:", cost_winner)

    english_df = pd.read_csv(ENGLISH_LOG)
    multilingual_df = pd.read_csv(MULTI_LOG)

    english_summary_df = calculate_sequential_summary(english_df)
    multilingual_summary_df = multilingual_df[multilingual_df["status"] == "Success"]

    multilingual_summary_df = multilingual_summary_df.groupby(["language","model"]).agg(
        avg_latency_ms=("latency_seconds", lambda x: round(x.mean()*1000,2)),
        p95_latency_ms=("latency_seconds", lambda x: round(x.quantile(0.95)*1000,2)),
        std_dev_ms=("latency_seconds", lambda x: round(x.std()*1000,2)),
        min_latency_ms=("latency_seconds", lambda x: round(x.min()*1000,2)),
        max_latency_ms=("latency_seconds", lambda x: round(x.max()*1000,2)),
        throughput_req_per_sec=("latency_seconds", lambda x: round(len(x)/(x.sum()),2))
    ).reset_index()

    # Optional concurrency
    try:
        concurrency_summary_df = pd.read_csv("../logs/concurrency_summary.csv")
    except:
        concurrency_summary_df = None
    # Final Excel
    with pd.ExcelWriter(FINAL_REPORT, engine="xlsxwriter") as writer:

        # Detailed sheets
        english_detailed_df.to_excel(writer, sheet_name="English Detailed", index=False)
        multilingual_detailed_df.to_excel(writer, sheet_name="Multilingual Detailed", index=False)

        workbook = writer.book

        # =========================
        # FORMAT ENGLISH DETAILED
        # =========================
        ws_eng = writer.sheets["English Detailed"]

        header_format = workbook.add_format({
            "bold": True,
            "border": 1,
            "align": "center",
            "valign": "middle",
            "bg_color": "#D9E1F2"
        })

        for col_num, col_name in enumerate(english_detailed_df.columns):
            ws_eng.write(0, col_num, col_name, header_format)
            ws_eng.set_column(col_num, col_num, 22)

        ws_eng.freeze_panes(1, 0)

        # =========================
        # FORMAT MULTILINGUAL DETAILED
        # =========================
        ws_multi = writer.sheets["Multilingual Detailed"]

        for col_num, col_name in enumerate(multilingual_detailed_df.columns):
            ws_multi.write(0, col_num, col_name, header_format)
            ws_multi.set_column(col_num, col_num, 22)

        ws_multi.freeze_panes(1, 0)

        # Raw and summary sheets
        # english_df.to_excel(writer, sheet_name="English Raw", index=False)
        # multilingual_df.to_excel(writer, sheet_name="Multilingual Raw", index=False)
        worksheet_seq = workbook.add_worksheet("Sequential Summary")

        header_format = workbook.add_format({
            "bold": True,
            "border": 1,
            "align": "center",
            "valign": "middle",
            "bg_color": "#D9E1F2"
        })

        cell_format = workbook.add_format({
            "border": 1,
            "align": "center"
        })

        winner_format = workbook.add_format({
            "border": 1,
            "align": "center",
            "bold": True,
            "bg_color": "#C6EFCE"
        })

        # =========================
        # ENGLISH SUMMARY
        # =========================
        worksheet_seq.write(0,0,"English Sequential Summary")

        english_summary_df.to_excel(
            writer,
            sheet_name="Sequential Summary",
            startrow=2,
            index=False
        )

        for col_num, col_name in enumerate(english_summary_df.columns):
            worksheet_seq.write(2, col_num, col_name, header_format)
            worksheet_seq.set_column(col_num, col_num, 22)

        # =========================
        # MULTILINGUAL SUMMARY
        # =========================
        start_row_multi = len(english_summary_df) + 6

        worksheet_seq.write(start_row_multi,0,"Multilingual Sequential Summary")

        multilingual_summary_df.to_excel(
            writer,
            sheet_name="Sequential Summary",
            startrow=start_row_multi + 2,
            index=False
        )

        for col_num, col_name in enumerate(multilingual_summary_df.columns):
            worksheet_seq.write(start_row_multi + 2, col_num, col_name, header_format)
        # =========================
        # SEQUENTIAL WINNER TABLE
        # =========================

        avg_latency_eng = english_summary_df.set_index("model")["avg_latency_ms"]
        throughput_eng = english_summary_df.set_index("model")["throughput_req_per_sec"]


        winner_latency_eng = "ElevenLabs" if avg_latency_eng["ElevenLabs"] < avg_latency_eng["Sarvam"] else "Sarvam"
        winner_tp_eng = "ElevenLabs" if throughput_eng["ElevenLabs"] > throughput_eng["Sarvam"] else "Sarvam"

        winner_start = start_row_multi + len(multilingual_summary_df) + 8

        worksheet_seq.write(winner_start,0,"English Benchmark Winner Summary")

        worksheet_seq.write(winner_start+1,0,"Metric",header_format)
        worksheet_seq.write(winner_start+1,1,"Better Model",header_format)

        worksheet_seq.write(winner_start+2,0,"Lowest Avg Latency",cell_format)
        worksheet_seq.write(winner_start+2,1,winner_latency_eng,winner_format)

        worksheet_seq.write(winner_start+3,0,"Highest Throughput",cell_format)
        worksheet_seq.write(winner_start+3,1,winner_tp_eng,winner_format)
        worksheet_seq.write(winner_start+4,0,"Lowest Cost",cell_format)
        worksheet_seq.write(winner_start+4,1,cost_winner,winner_format)
        # =========================
        # =========================
        # MULTILINGUAL WINNER TABLE
        # =========================

        avg_latency_multi = multilingual_df.groupby("model")["latency_seconds"].mean()*1000
        throughput_multi = multilingual_df.groupby("model")["latency_seconds"].apply(lambda x: len(x)/x.sum())

        winner_latency_multi = "ElevenLabs" if avg_latency_multi["ElevenLabs"] < avg_latency_multi["Sarvam"] else "Sarvam"
        winner_tp_multi = "ElevenLabs" if throughput_multi["ElevenLabs"] > throughput_multi["Sarvam"] else "Sarvam"

        multi_winner_start = winner_start + 7

        worksheet_seq.write(multi_winner_start,0,"Multilingual Benchmark Winner Summary")

        worksheet_seq.write(multi_winner_start+1,0,"Metric",header_format)
        worksheet_seq.write(multi_winner_start+1,1,"Better Model",header_format)

        worksheet_seq.write(multi_winner_start+2,0,"Lowest Avg Latency",cell_format)
        worksheet_seq.write(multi_winner_start+2,1,winner_latency_multi,winner_format)

        worksheet_seq.write(multi_winner_start+3,0,"Highest Throughput",cell_format)
        worksheet_seq.write(multi_winner_start+3,1,winner_tp_multi,winner_format)
        

        # Concurrency summary (if available)
        if concurrency_summary_df is not None:

            concurrency_summary_df.to_excel(
                writer,
                sheet_name="Concurrency Summary",
                startrow=0,
                index=False
            )

            worksheet = writer.sheets["Concurrency Summary"]
            worksheet.set_column(0, 12, 22)

            # =========================
            # FORMATTING
            # =========================
            header_format = workbook.add_format({
                "bold": True,
                "border": 1,
                "align": "center",
                "valign": "middle",
                "bg_color": "#D9E1F2"
            })

            cell_format = workbook.add_format({
                "border": 1,
                "align": "center"
            })

            winner_format = workbook.add_format({
                "border": 1,
                "align": "center",
                "bold": True,
                "bg_color": "#C6EFCE"
            })

            # Format main table headers
            for col_num, col_name in enumerate(concurrency_summary_df.columns):
                worksheet.write(0, col_num, col_name, header_format)
                worksheet.set_column(col_num, col_num, 18)

            # =========================
            # MODEL COMPARISON SUMMARY
            # =========================
            avg_latency = concurrency_summary_df.groupby("model")["avg_latency_ms"].mean()
            avg_p95 = concurrency_summary_df.groupby("model")["p95_latency_ms"].mean()
            avg_throughput = concurrency_summary_df.groupby("model")["throughput_req_per_sec"].mean()

            summary_start = len(concurrency_summary_df) + 8

            worksheet.write(summary_start, 0, "Model Comparison Summary")

            worksheet.write(summary_start + 1, 0, "Metric", header_format)
            worksheet.write(summary_start + 1, 1, "ElevenLabs", header_format)
            worksheet.write(summary_start + 1, 2, "Sarvam", header_format)
            worksheet.write(summary_start + 1, 3, "Better Model", header_format)

            # Avg Latency (lower is better)
            worksheet.write(summary_start + 2, 0, "Average Latency (ms)", cell_format)
            worksheet.write(summary_start + 2, 1, avg_latency.get("ElevenLabs", 0), cell_format)
            worksheet.write(summary_start + 2, 2, avg_latency.get("Sarvam", 0), cell_format)

            better_latency = "ElevenLabs" if avg_latency.get("ElevenLabs", 0) < avg_latency.get("Sarvam", 0) else "Sarvam"
            worksheet.write(summary_start + 2, 3, better_latency, winner_format)

            # P95 Latency
            worksheet.write(summary_start + 3, 0, "Average P95 Latency (ms)", cell_format)
            worksheet.write(summary_start + 3, 1, avg_p95.get("ElevenLabs", 0), cell_format)
            worksheet.write(summary_start + 3, 2, avg_p95.get("Sarvam", 0), cell_format)

            better_p95 = "ElevenLabs" if avg_p95.get("ElevenLabs", 0) < avg_p95.get("Sarvam", 0) else "Sarvam"
            worksheet.write(summary_start + 3, 3, better_p95, winner_format)

            # Throughput (higher is better)
            worksheet.write(summary_start + 4, 0, "Average Throughput (req/sec)", cell_format)
            worksheet.write(summary_start + 4, 1, avg_throughput.get("ElevenLabs", 0), cell_format)
            worksheet.write(summary_start + 4, 2, avg_throughput.get("Sarvam", 0), cell_format)

            better_tp = "ElevenLabs" if avg_throughput.get("ElevenLabs", 0) > avg_throughput.get("Sarvam", 0) else "Sarvam"
            worksheet.write(summary_start + 4, 3, better_tp, winner_format)

        # =========================
        # PROPER NOUN SHEET (if available)
        # =========================
        if os.path.exists(PROPER_NOUN_LOG):

            proper_df = pd.read_csv(PROPER_NOUN_LOG)
            proper_df = proper_df[proper_df["status"] == "Success"]

            # Extract unique test id from output file (proper_1, proper_2, etc.)
            proper_df["test_id"] = proper_df["output_file"].str.extract(r'proper_(\d+)').astype(int)

            proper_pivot = proper_df.pivot(
                index=["test_id", "phrase"],
                columns="model",
                values="latency_ms"
            ).reset_index()

            proper_pivot = proper_pivot.sort_values("test_id")

            proper_pivot.columns.name = None
            proper_pivot = proper_pivot.rename(columns={
                "phrase": "Phrase",
                "ElevenLabs": "Eleven Latency (ms)",
                "Sarvam": "Sarvam Latency (ms)"
            })

            # =========================
            # Latency Winner
            # =========================
            def latency_winner(row):
                if row["Eleven Latency (ms)"] < row["Sarvam Latency (ms)"]:
                    return "ElevenLabs"
                elif row["Eleven Latency (ms)"] > row["Sarvam Latency (ms)"]:
                    return "Sarvam"
                else:
                    return "Tie"

            proper_pivot["Latency Winner"] = proper_pivot.apply(latency_winner, axis=1)

            # =========================
            # Merge manual ratings
            # =========================
            # Merge manual ratings
            # =========================
            MANUAL_RATING_CSV = "../logs/propernoun_manual_ratings.csv"

            if os.path.exists(MANUAL_RATING_CSV):

                ratings_df = pd.read_csv(MANUAL_RATING_CSV)

                # extract id from proper_1 → 1
                ratings_df["test_id"] = ratings_df["phrase"].str.extract(r'proper_(\d+)').astype(int)

                proper_pivot = proper_pivot.merge(
                    ratings_df,
                    on="test_id",
                    how="left"
                )

                proper_pivot.rename(columns={
                    "eleven_score": "Eleven Pronunciation",
                    "sarvam_score": "Sarvam Pronunciation"
                }, inplace=True)

                proper_pivot.drop(columns=["phrase","better_model"], inplace=True)

            else:
                proper_pivot["Eleven Pronunciation"] = ""
                proper_pivot["Sarvam Pronunciation"] = ""

            # =========================
            # Pronunciation Winner
            # =========================
            def pronunciation_winner(row):
                try:
                    e = float(row["Eleven Pronunciation"])
                    s = float(row["Sarvam Pronunciation"])

                    if e > s:
                        return "ElevenLabs"
                    elif s > e:
                        return "Sarvam"
                    else:
                        return "Tie"
                except:
                    return ""

            proper_pivot["Pronunciation Winner"] = proper_pivot.apply(pronunciation_winner, axis=1)

            # Add Notes column
            proper_pivot["Notes"] = ""

            # Clean column order
            proper_pivot = proper_pivot[
                [
                    "test_id",
                    "Phrase",
                    "Eleven Latency (ms)",
                    "Sarvam Latency (ms)",
                    "Latency Winner",
                    "Eleven Pronunciation",
                    "Sarvam Pronunciation",
                    "Pronunciation Winner",
                    "Notes"
                ]
            ]

            # =========================
            # BENCHMARK SUMMARY
            # =========================
            avg_eleven = round(proper_pivot["Eleven Latency (ms)"].mean(), 2)
            avg_sarvam = round(proper_pivot["Sarvam Latency (ms)"].mean(), 2)

            latency_winner_model = "ElevenLabs" if avg_eleven < avg_sarvam else "Sarvam"

            eleven_pron = pd.to_numeric(proper_pivot["Eleven Pronunciation"], errors="coerce").mean()
            sarvam_pron = pd.to_numeric(proper_pivot["Sarvam Pronunciation"], errors="coerce").mean()

            if pd.isna(eleven_pron) or pd.isna(sarvam_pron):
                pron_winner = ""
            else:
                pron_winner = "ElevenLabs" if eleven_pron > sarvam_pron else "Sarvam"

            summary_rows = [
                ["PROPER NOUN BENCHMARK SUMMARY"],
                ["-------------------------------------------------"],
                [f"Average Eleven Latency: {avg_eleven} ms"],
                [f"Average Sarvam Latency: {avg_sarvam} ms"],
                [f"Latency Winner: {latency_winner_model}"],
                [f"Pronunciation Winner: {pron_winner}"],
                ["-------------------------------------------------"],
                ["Detailed Evaluation"],
                []
            ]

            summary_df = pd.DataFrame(summary_rows)

            # Write summary first
            summary_df.to_excel(
                writer,
                sheet_name="Proper Noun Evaluation",
                index=False,
                header=False
            )

            # Write detailed table below summary
            proper_pivot.to_excel(
                writer,
                sheet_name="Proper Noun Evaluation",
                startrow=len(summary_rows),
                index=False
            )
            #-------------------------------------------

            # =========================
            # Improve Excel Formatting
            # =========================
            worksheet = writer.sheets["Proper Noun Evaluation"]

            # Adjust column widths
            worksheet.set_column("A:A", 8)    # test_id
            worksheet.set_column("B:B", 28)   # Phrase
            worksheet.set_column("C:D", 18)   # Latency columns
            worksheet.set_column("E:E", 16)   # Latency Winner
            worksheet.set_column("F:G", 20)   # Pronunciation scores
            worksheet.set_column("H:H", 22)   # Pronunciation Winner
            worksheet.set_column("I:I", 20)   # Notes

            # Freeze header row
            worksheet.freeze_panes(len(summary_rows)+1, 0)

    print("Final professional benchmark report created!")