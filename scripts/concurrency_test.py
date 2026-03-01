import concurrent.futures
import statistics
import csv
import os
import traceback
from elevenlabs_api import generate_elevenlabs_audio
from sarvam_api import generate_sarvam_audio

VOICE_ID = "vYENaCJHl4vFKNDYPr8y"
DATASET_PATH = "../dataset/english_50_concurrency.txt"
OUTPUT_FILE = "../logs/concurrency_summary.csv"

CONCURRENCY_LEVELS = [5, 10]


def load_dataset():
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found:", DATASET_PATH)
        return []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def calculate_p95(data):
    sorted_data = sorted(data)
    index = int(0.95 * len(sorted_data)) - 1
    return sorted_data[max(index, 0)]


def run_test_for_model(model_name, func, dataset, concurrency_level):
    latencies = []
    failures = 0

    for i in range(0, len(dataset), concurrency_level):
        batch = dataset[i:i + concurrency_level]

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_level) as executor:
            futures = [executor.submit(func, text) for text in batch]

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=60)

                    # Handle both 2-value and 3-value return safely
                    if isinstance(result, tuple) and len(result) >= 2:
                        success = result[0]
                        latency = result[1]
                    else:
                        print("Unexpected result format:", result)
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

    return latencies, failures


def eleven_wrapper(text):
    return generate_elevenlabs_audio(text, VOICE_ID, None)


def sarvam_wrapper(text):
    return generate_sarvam_audio(text, None)


def run_concurrency_tests():
    dataset = load_dataset()

    if not dataset:
        print("Dataset empty. Exiting.")
        return

    summary_rows = []

    for level in CONCURRENCY_LEVELS:
        print(f"\nRunning concurrency level: {level}")

        for model_name, func in [
            ("ElevenLabs", eleven_wrapper),
            ("Sarvam", sarvam_wrapper)
        ]:
            latencies, failures = run_test_for_model(
                model_name, func, dataset, level
            )

            total_requests = len(dataset)
            success_count = len(latencies)

            if latencies:
                avg = statistics.mean(latencies)
                std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
                p95 = calculate_p95(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                total_time_sec = sum(latencies) / 1000
                throughput = success_count / total_time_sec if total_time_sec > 0 else 0
            else:
                avg = std_dev = p95 = max_latency = min_latency = throughput = 0

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
                round(std_dev, 2),
                round(min_latency, 2),
                round(max_latency, 2),
                round(throughput, 2)
            ])

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
            "std_dev_ms",
            "min_latency_ms",
            "max_latency_ms",
            "throughput_req_per_sec"
        ])
        writer.writerows(summary_rows)

    print("\nConcurrency summary generated.")


if __name__ == "__main__":
    run_concurrency_tests()