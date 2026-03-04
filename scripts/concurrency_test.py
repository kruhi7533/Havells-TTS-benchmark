import concurrent.futures
import statistics
import csv
import os
import time
import traceback
import numpy as np

from elevenlabs_api import generate_elevenlabs_audio
from sarvam_api import generate_sarvam_audio


VOICE_ID = "vYENaCJHl4vFKNDYPr8y"

DATASET_PATH = "../dataset/english_50_concurrency.txt"
OUTPUT_FILE = "../logs/concurrency_summary.csv"

# Recommended benchmark levels
CONCURRENCY_LEVELS = [1, 5, 10, 20]


# ================================
# LOAD DATASET
# ================================
def load_dataset():
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found:", DATASET_PATH)
        return []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# ================================
# WRAPPERS
# ================================
def eleven_wrapper(text):
    return generate_elevenlabs_audio(text, VOICE_ID, None)


def sarvam_wrapper(text):
    return generate_sarvam_audio(text, None)


# ================================
# WARMUP
# ================================
def warmup():
    print("\nRunning warmup requests...")

    try:
        eleven_wrapper("Warmup request")
    except:
        pass

    try:
        sarvam_wrapper("Warmup request")
    except:
        pass


# ================================
# CONCURRENCY TEST
# ================================
def run_test_for_model(model_name, func, dataset, concurrency_level):

    latencies = []
    failures = 0

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_level) as executor:

        futures = [executor.submit(func, text) for text in dataset]

        for future in concurrent.futures.as_completed(futures):

            try:
                result = future.result(timeout=120)

                if isinstance(result, tuple) and len(result) >= 2:
                    success = result[0]
                    latency = result[1]
                else:
                    failures += 1
                    continue

                if success:
                    latencies.append(latency * 1000)
                else:
                    failures += 1

            except Exception as e:
                print(f"[{model_name}] ERROR:", str(e))
                traceback.print_exc()
                failures += 1

    end_time = time.time()

    total_runtime = end_time - start_time

    return latencies, failures, total_runtime


# ================================
# MAIN TEST
# ================================
def run_concurrency_tests():

    dataset = load_dataset()

    if not dataset:
        print("Dataset empty. Exiting.")
        return

    warmup()

    summary_rows = []

    for level in CONCURRENCY_LEVELS:

        print(f"\nRunning concurrency level: {level}")

        for model_name, func in [
            ("ElevenLabs", eleven_wrapper),
            ("Sarvam", sarvam_wrapper)
        ]:

            latencies, failures, runtime = run_test_for_model(
                model_name, func, dataset, level
            )

            total_requests = len(dataset)
            success_count = len(latencies)

            if latencies:

                avg = statistics.mean(latencies)
                std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0

                p95 = np.percentile(latencies, 95)
                p99 = np.percentile(latencies, 99)

                max_latency = max(latencies)
                min_latency = min(latencies)

                throughput = success_count / runtime

            else:

                avg = std_dev = p95 = p99 = max_latency = min_latency = throughput = 0

            failure_rate = (failures / total_requests) * 100

            summary_rows.append([
                model_name,
                level,
                total_requests,
                success_count,
                failures,
                round(failure_rate, 2),
                round(avg, 2),
                round(p95, 2),
                round(p99, 2),
                round(std_dev, 2),
                round(min_latency, 2),
                round(max_latency, 2),
                round(throughput, 2)
            ])

            print(
                f"{model_name} | "
                f"Success: {success_count}/{total_requests} | "
                f"Avg Latency: {round(avg,2)} ms | "
                f"Throughput: {round(throughput,2)} req/s"
            )

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "model",
            "concurrency_level",
            "total_requests",
            "successful_requests",
            "failed_requests",
            "failure_rate_percent",
            "avg_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "std_dev_ms",
            "min_latency_ms",
            "max_latency_ms",
            "throughput_req_per_sec"
        ])

        writer.writerows(summary_rows)

    print("\nConcurrency summary generated at:", OUTPUT_FILE)


# ================================
# ENTRY POINT
# ================================
if __name__ == "__main__":
    run_concurrency_tests()