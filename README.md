# TTS Latency & Quality Benchmark Suite

This repository contains a comprehensive benchmarking and evaluation suite for Text-to-Speech (TTS) models (specifically focusing on **ElevenLabs** and **Sarvam AI**). The suite allows you to measure Time-to-First-Audio (TTFA) latency, test system concurrency limits, and conduct human evaluation surveys on audio quality.

---

## 📂 Project Structure

```text
├── dataset/                        # Text datasets used for sequential benchmarks
├── logs/                           # CSV logs and Excel summaries for sequential runner
├── outputs/                        # Output generated audio wav/mp3 files
├── sarvam_ttfa_concurrency/        # Concurrency & load-testing suite for Sarvam WebSocket API
│   ├── dataset/                    # Language-wise text files for load testing (English, Hindi, Telugu, etc.)
│   ├── logs/                       # Raw outputs, summaries, and latency stats
│   ├── concurrency_test.py         # Parallel load-testing simulation (C=1, 5, 10, 20)
│   ├── export_results.py           # Exports load test outcomes to Excel
│   ├── sarvam_api.py               # Async WebSocket connection wrapper for Sarvam bulbul:v3
│   └── ttfa_runner.py              # Sequential latency collector across all 8 languages
├── scripts/                        # Sequential execution scripts
│   ├── elevenlabs_api.py           # ElevenLabs API integration wrapper
│   ├── sarvam_api.py               # Sarvam REST API integration wrapper
│   └── runner.py                   # Main runner for sequential benchmarks
├── analyze_latency.py              # Computes comparative metrics and exports to Excel
├── manual_testing.py               # Streamlit application for human-in-the-loop rating & stats
├── ratings.csv                     # Database of human evaluation scores
└── requirements.txt                # Project dependencies
```

---

## 🚀 Setup & Installation

### 1. Pre-requisites
Ensure you have Python 3.10+ installed.

### 2. Install Dependencies
Set up a virtual environment (optional but recommended) and install the packages:
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API Keys
The benchmarking tools look for API keys set in your environment. You can set them like so:

**PowerShell (Windows):**
```powershell
$env:ELEVENLABS_API_KEY="your-elevenlabs-key"
$env:SARVAM_API_KEY="your-sarvam-key"
```

**Bash (Linux/macOS):**
```bash
export ELEVENLABS_API_KEY="your-elevenlabs-key"
export SARVAM_API_KEY="your-sarvam-key"
```

---

## 🏃 Running the Benchmarks

### 1. Sequential Latency Benchmark (ElevenLabs vs Sarvam)
Run the sequential runner to generate audios from your dataset and record latencies:
```bash
python scripts/runner.py
```
> [!NOTE]
> This script updates its progress state in `logs/english_progress.json` to allow resumption of runs.

After completion, generate the Excel summary report containing average TTFA, raw logs, and model comparison details:
```bash
python analyze_latency.py
```
The summaries will be stored under `logs/english_latency_summary.xlsx`.

---

### 2. Streamlit Human Evaluation Dashboard
Conduct naturalness, clarity, pronunciation, and consistency ratings on generated audios:
```bash
streamlit run manual_testing.py
```
This launches a browser-based UI containing:
- An audio player to play generated clips.
- Inputs to evaluate quality on a scale of 1–5.
- Real-time statistics including leaderboards, average parameters per model, and language-wise analysis.

---

### 3. Sarvam Concurrency & Multi-Language Testing
To stress test the Sarvam WebSocket API across different languages:

- **Run sequential latency check for all 8 Indian languages:**
  ```bash
  python sarvam_ttfa_concurrency/ttfa_runner.py
  ```
- **Run load tests with varying concurrency levels (1, 5, 10, 20 parallel threads):**
  ```bash
  python sarvam_ttfa_concurrency/concurrency_test.py
  ```
- **Export concurrency stats (throughput, P50, P95, P99 latencies) to Excel:**
  ```bash
  python sarvam_ttfa_concurrency/export_results.py
  ```
