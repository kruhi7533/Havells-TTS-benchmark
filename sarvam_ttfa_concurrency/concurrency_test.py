import asyncio
import statistics
import time
import numpy as np
import os
import csv

from sarvam_api import generate_tts_async, LANGUAGE_CODES

LANGUAGES = list(LANGUAGE_CODES.keys())  # 🔥 AUTO SYNC ALL LANGUAGES
CONCURRENCY_LEVELS = [1, 5, 10, 20]
MAX_SENTENCES = 50

LOG_DIR = "logs"
OUTPUT_FILE = os.path.join(LOG_DIR, "concurrency_summary.csv")
os.makedirs(LOG_DIR, exist_ok=True)


def load_dataset(language):
    path = f"dataset/{language}.txt"

    if not os.path.exists(path):
        path = f"dataset/{language.capitalize()}.txt"

    if not os.path.exists(path):
        print(f"Dataset missing: {language}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()][:MAX_SENTENCES]


async def run_test(dataset, language, concurrency):

    semaphore = asyncio.Semaphore(concurrency)

    async def task(text):
        async with semaphore:
            return await generate_tts_async(text, language)

    start = time.perf_counter()

    results = await asyncio.gather(
        *[task(text) for text in dataset],
        return_exceptions=True
    )

    end = time.perf_counter()

    ttfa_list = []
    failures = 0

    for r in results:
        if isinstance(r, Exception):
            failures += 1
            continue

        success, ttfa, _, _ = r

        if success:
            ttfa_list.append(ttfa * 1000)
        else:
            failures += 1

    duration = end - start
    success_count = len(ttfa_list)

    def p(x):
        return np.percentile(ttfa_list, x) if ttfa_list else 0

    return {
        "total": len(dataset),
        "success": success_count,
        "failures": failures,
        "avg_ttfa": statistics.mean(ttfa_list) if ttfa_list else 0,
        "p50": p(50),
        "p95": p(95),
        "p99": p(99),
        "throughput": success_count / duration if duration > 0 else 0
    }


async def main():

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "language", "concurrency_level",
            "total", "success", "failures",
            "failure_rate_percent",
            "avg_ttfa_ms", "p50", "p95", "p99",
            "throughput"
        ])

        for lang in LANGUAGES:
            dataset = load_dataset(lang)

            if not dataset:
                continue

            print(f"\nLanguage: {lang}")

            for c in CONCURRENCY_LEVELS:
                metrics = await run_test(dataset, lang, c)

                print(
                    f"C={c} | Avg={metrics['avg_ttfa']:.2f} ms | "
                    f"P95={metrics['p95']:.2f} | "
                    f"Throughput={metrics['throughput']:.2f}/s"
                )

                failure_rate = round(
                    (metrics["failures"] / metrics["total"] * 100)
                    if metrics["total"] > 0 else 0, 2
                )

                writer.writerow([
                    lang, c,
                    metrics["total"],
                    metrics["success"],
                    metrics["failures"],
                    failure_rate,
                    round(metrics["avg_ttfa"], 2),
                    round(metrics["p50"], 2),
                    round(metrics["p95"], 2),
                    round(metrics["p99"], 2),
                    round(metrics["throughput"], 2)
                ])


if __name__ == "__main__":
    asyncio.run(main())