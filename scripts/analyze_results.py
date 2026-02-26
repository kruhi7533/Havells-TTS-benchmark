import csv
import math
from collections import defaultdict

INPUT_FILE = "../logs/latency_raw.csv"
OUTPUT_FILE = "../logs/latency_summary.csv"

latencies = defaultdict(list)
total_requests = defaultdict(int)
failed_requests = defaultdict(int)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        model = row["model"]
        latency = float(row["latency_seconds"]) * 1000  # convert to ms
        status = row["status"]

        total_requests[model] += 1

        if status != "Success":
            failed_requests[model] += 1
        else:
            latencies[model].append(latency)

summary_rows = []

for model in total_requests:
    success = total_requests[model] - failed_requests[model]
    success_rate = (success / total_requests[model]) * 100
    failure_rate = (failed_requests[model] / total_requests[model]) * 100

    if latencies[model]:
        lat_list = latencies[model]

        avg_latency = sum(lat_list) / len(lat_list)
        min_latency = min(lat_list)
        max_latency = max(lat_list)

        # Std deviation
        variance = sum((x - avg_latency) ** 2 for x in lat_list) / len(lat_list)
        std_dev = math.sqrt(variance)

        # P95
        sorted_lat = sorted(lat_list)
        index_95 = int(0.95 * len(sorted_lat)) - 1
        p95_latency = sorted_lat[max(index_95, 0)]

        # Throughput
        total_time_sec = sum(lat_list) / 1000
        throughput = success / total_time_sec if total_time_sec > 0 else 0

    else:
        avg_latency = min_latency = max_latency = std_dev = p95_latency = throughput = 0

    summary_rows.append([
        model,
        total_requests[model],
        success,
        failed_requests[model],
        round(success_rate, 2),
        round(failure_rate, 2),
        round(avg_latency, 2),
        round(p95_latency, 2),
        round(std_dev, 2),
        round(min_latency, 2),
        round(max_latency, 2),
        round(throughput, 2)
    ])

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "model",
        "total_requests",
        "successful_requests",
        "failed_requests",
        "success_rate_percent",
        "failure_rate_percent",
        "avg_latency_ms",
        "p95_latency_ms",
        "std_dev_ms",
        "min_latency_ms",
        "max_latency_ms",
        "throughput_req_per_sec"
    ])
    writer.writerows(summary_rows)

print("Professional summary generated at:", OUTPUT_FILE)