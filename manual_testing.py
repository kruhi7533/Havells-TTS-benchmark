import streamlit as st
import pandas as pd
import os
from pathlib import Path
import re

st.set_page_config(page_title="TTS Evaluation Tool", layout="wide")

RATINGS_FILE = "ratings.csv"

AUDIO_EXTENSIONS = (".wav", ".mp3", ".mpeg")

SOURCE_DIRS = {
    "sarvam": ["outputs/sarvam/Kannada"],
    "elevenlabs": ["outputs/elevenlabs/Telugu"],
}


def normalize_path(p):
    return str(Path(p)).replace("\\", "/").lower()


def get_source_dir(source):
    for c in SOURCE_DIRS[source]:
        p = Path(c)
        if p.exists() and p.is_dir():
            return p
    return None


def get_audio_files(source):
    d = get_source_dir(source)
    if not d:
        return []

    files = [
        p for p in d.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]

    # Keep numeric sequence stable: english_2 comes before english_10.
    return sorted(files, key=audio_sort_key)


def audio_sort_key(path_obj):
    stem = path_obj.stem.lower()
    match = re.search(r"_(\d+)$", stem)
    idx = int(match.group(1)) if match else float("inf")
    return (stem.rsplit("_", 1)[0], idx, path_obj.name.lower())


def get_text_mapping(dataset_file):
    if not dataset_file:
        return {}
    p = Path(dataset_file)
    if not p.exists() or not p.is_file():
        return {}

    with p.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]

    return {i: line for i, line in enumerate(lines)}


def get_audio_index_from_name(path_obj):
    match = re.search(r"_(\d+)$", path_obj.stem.lower())
    return int(match.group(1)) if match else None


def find_dataset_file_for_audio(path_obj):
    stem = path_obj.stem
    base = re.sub(r"_\d+$", "", stem, flags=re.IGNORECASE)
    candidates = [
        Path("dataset") / f"{base}.txt",
        Path("dataset") / f"{base.lower()}.txt",
        Path("dataset") / f"{base.capitalize()}.txt",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def load_ratings():
    if not os.path.exists(RATINGS_FILE):
        return pd.DataFrame()

    df = pd.read_csv(RATINGS_FILE)

    if "model" not in df.columns:
        df["model"] = "unknown"

    if "audio_path" not in df.columns and "audio" in df.columns:
        df["audio_path"] = df["audio"]

    return df


st.title("🎧 TTS Human Evaluation Tool")

st.sidebar.title("Settings")

developer_mode = st.sidebar.checkbox("Developer Mode")

if developer_mode:
    if st.sidebar.button("Reset Evaluation Data"):
        if os.path.exists(RATINGS_FILE):
            os.remove(RATINGS_FILE)
        st.success("All ratings cleared")
        st.rerun()


if "audio_index" not in st.session_state:
    st.session_state.audio_index = 0

if "audio_source" not in st.session_state:
    st.session_state.audio_source = "sarvam"

audio_source = st.selectbox(
    "Choose Audio Source",
    ["sarvam", "elevenlabs"],
)

if audio_source != st.session_state.audio_source:
    st.session_state.audio_source = audio_source
    st.session_state.audio_index = 0

# Load Data
audio_files = get_audio_files(audio_source)
ratings_df = load_ratings()

rated_paths = set()

if not ratings_df.empty:
    rated_subset = ratings_df[
        ratings_df["model"] == audio_source
    ]

    rated_paths = {
        normalize_path(p)
        for p in rated_subset["audio_path"]
    }

# Evaluation Section
if audio_files:

    total_files = len(audio_files)

    if st.session_state.audio_index >= total_files:
        st.session_state.audio_index = total_files - 1

    current_file = audio_files[
        st.session_state.audio_index
    ]

    current_key = normalize_path(str(current_file))
    already_rated = current_key in rated_paths

    st.subheader(
        f"Audio {st.session_state.audio_index+1}/{total_files}"
    )
    st.caption(f"File: {current_file.name}")

    if already_rated:
        st.info("Already rated")

    st.audio(str(current_file))

    if developer_mode:
        st.markdown("### Developer Verification")

        selected_name = st.selectbox(
            "Select Any Audio",
            options=[f.name for f in audio_files],
            index=st.session_state.audio_index,
            key="dev_audio_select",
        )

        selected_file = next(
            (f for f in audio_files if f.name == selected_name),
            current_file
        )

        selected_idx = audio_files.index(selected_file)

        if selected_idx != st.session_state.audio_index:
            st.session_state.audio_index = selected_idx
            st.rerun()

        dataset_file = find_dataset_file_for_audio(current_file)
        audio_line_idx = get_audio_index_from_name(current_file)
        text_map = get_text_mapping(dataset_file)

        if dataset_file is not None:
            st.caption(f"Dataset: {dataset_file}")
            if audio_line_idx is not None and audio_line_idx in text_map:
                st.info(
                    f"Text #{audio_line_idx}: {text_map[audio_line_idx]}"
                )
            elif audio_line_idx is not None:
                st.warning(
                    f"No text line found for index {audio_line_idx} in {dataset_file.name}"
                )
            else:
                st.warning("Could not parse numeric index from audio filename.")
        else:
            st.warning("No matching dataset text file found for this audio.")

    st.markdown("### Rate Audio")

    c1, c2 = st.columns(2)

    with c1:
        naturalness = st.slider("Naturalness", 1, 5, 3)
        clarity = st.slider("Clarity", 1, 5, 3)

    with c2:
        pronunciation = st.slider("Pronunciation", 1, 5, 3)
        consistency = st.slider("Consistency", 1, 5, 3)

    b1, b2, b3 = st.columns(3)

    with b1:
        label = "Update Rating" if already_rated else "Submit Rating"

        if st.button(label):

            new_row = pd.DataFrame([{
                "model": audio_source,
                "audio": current_file.name,
                "audio_path": str(current_file),
                "naturalness": naturalness,
                "clarity": clarity,
                "pronunciation": pronunciation,
                "consistency": consistency
            }])

            if os.path.exists(RATINGS_FILE):
                old = load_ratings()

                old = old[
                    ~(
                        (old["model"] == audio_source)
                        &
                        (
                            old["audio_path"]
                            .map(normalize_path)
                            == current_key
                        )
                    )
                ]

                df = pd.concat([old, new_row])
            else:
                df = new_row

            df.to_csv(RATINGS_FILE, index=False)

            st.success("Rating Saved")

    # NEXT
    with b2:
        if st.button("Next Audio"):
            if st.session_state.audio_index < total_files - 1:
                st.session_state.audio_index += 1
                st.rerun()

    # SKIP RATED BUTTON (NORMAL MODE ONLY)
    with b3:
        if (
            not developer_mode
            and st.button("Skip Rated Audio")
        ):

            next_idx = None

            for i, f in enumerate(audio_files):
                if normalize_path(str(f)) not in rated_paths:
                    next_idx = i
                    break

            if next_idx is not None:
                st.session_state.audio_index = next_idx
                st.rerun()
            else:
                st.warning("All audios already rated")

else:
    st.warning("No audio files found.")


# STATISTICS DASHBOARD
st.markdown("---")
st.header("📊 Evaluation Statistics")

if os.path.exists(RATINGS_FILE):

    df = load_ratings()

    metrics = [
        "naturalness",
        "clarity",
        "pronunciation",
        "consistency",
    ]

    total = len(df)
    unique = df["audio_path"].nunique()

    avg_scores = df[metrics].mean()
    overall = avg_scores.mean()

    c1, c2, c3 = st.columns(3)

    c1.metric("Ratings Submitted", total)
    c2.metric("Unique Audios Rated", unique)
    c3.metric("Overall Avg", round(overall, 2))

    st.subheader("Parameter Averages")
    st.dataframe(avg_scores.round(2))

    # MODEL COMPARISON
    st.subheader("Model Benchmark Comparison")

    model_scores = df.groupby("model")[metrics].mean()
    model_scores["overall"] = model_scores.mean(axis=1)

    # Add count of audios tested for each model
    audio_counts = df.groupby("model")["audio_path"].nunique()
    model_scores["audio_count"] = audio_counts

    # Extract language from audio_path
    df['language'] = df['audio_path'].str.extract(r'outputs\\[^\\]+\\([^\\]+)\\')

    # Validate extracted language
    if df['language'].isnull().any():
        st.warning("Some audio paths have invalid or missing language information.")
        df = df.dropna(subset=['language'])

    # Add count of audios tested per language per model
    language_audio_counts = df.groupby(["model", "language"])["audio_path"].nunique()
    language_audio_counts = language_audio_counts.reset_index()
    language_audio_counts.columns = ["Model", "Language", "Audio Count"]

    st.dataframe(model_scores.round(2))

    st.subheader("Language-wise Audio Counts per Model")
    st.dataframe(language_audio_counts)

    if {"sarvam", "elevenlabs"}.issubset(model_scores.index):

        winner = model_scores["overall"].idxmax()

        st.success(
            f" Current Leader: {winner.upper()}"
        )

