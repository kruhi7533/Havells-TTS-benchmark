import pandas as pd
import statistics

INPUT_FILE = "../logs/english_latency_raw.csv"
OUTPUT_FILE = "../logs/sequential_summary.csv"

english_df = pd.read_csv(INPUT_FILE)

# Only success rows
# =========================
# CALCULATE SEQUENTIAL SUMMARY PER MODEL
# =========================

english_success = english_df[english_df["status"] == "Success"].copy()

summary_rows = []

for model_name in english_success["model"].unique():

    model_df = english_success[english_success["model"] == model_name]
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

english_summary_df = pd.DataFrame(summary_rows)

english_summary_df .to_csv(OUTPUT_FILE, index=False)

print("Sequential summary generated.")