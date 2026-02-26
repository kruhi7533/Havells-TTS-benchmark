import streamlit as st
import pandas as pd
import os
from pathlib import Path

st.set_page_config(
    page_title="TTS Evaluation Tool",
    layout="wide"
)

RATINGS_FILE = "ratings.csv"
AUDIO_EXTENSIONS = (".wav", ".mp3", ".mpeg")
SOURCE_DIRS = {
    "sarvam": ["dataset/sarvam", "outputs/sarvam"],
    "elevenlabs": ["dataset/elevenlabs", "outputs/elevenlabs"],
}


def normalize_path(path_value):
    return str(Path(path_value)).replace("\\", "/").lower()

st.markdown("""
<style>
[data-testid="stFileUploader"] {
    cursor: pointer !important;
}
[data-testid="stFileUploader"] * {
    cursor: pointer !important;
}
</style>
""", unsafe_allow_html=True)

st.title("TTS Human Evaluation Tool")

st.sidebar.title("Settings")

developer_mode = st.sidebar.checkbox("Developer Mode")

if developer_mode:
    if st.sidebar.button("Reset Evaluation Data"):
        if os.path.exists(RATINGS_FILE):
            os.remove(RATINGS_FILE)
        st.success("Dashboard Reset!")
        st.rerun()


def get_source_dir(source_name):
    for candidate in SOURCE_DIRS[source_name]:
        path = Path(candidate)
        if path.exists() and path.is_dir():
            return path
    return None


def get_audio_files(source_name):
    source_dir = get_source_dir(source_name)
    if source_dir is None:
        return []

    files = [
        p for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return sorted(files, key=lambda p: p.name.lower())


def load_ratings():
    if not os.path.exists(RATINGS_FILE):
        return pd.DataFrame()

    df = pd.read_csv(RATINGS_FILE)
    if "model" not in df.columns:
        df["model"] = "unknown"
    if "audio_path" not in df.columns and "audio" in df.columns:
        df["audio_path"] = df["audio"]
    return df


if "audio_index" not in st.session_state:
    st.session_state.audio_index = 0

if "audio_source" not in st.session_state:
    st.session_state.audio_source = "sarvam"

audio_source = st.selectbox(
    "Choose Audio Source",
    options=["sarvam", "elevenlabs"],
    index=0 if st.session_state.audio_source == "sarvam" else 1
)

if st.session_state.audio_source != audio_source:
    st.session_state.audio_source = audio_source
    st.session_state.audio_index = 0

audio_files = get_audio_files(audio_source)
source_dir = get_source_dir(audio_source)
ratings_df = load_ratings()

source_file_map = {normalize_path(str(p)): p for p in audio_files}
rated_paths_for_source = set()
if not ratings_df.empty and "audio_path" in ratings_df.columns:
    rated_df = ratings_df[ratings_df["model"] == audio_source] if "model" in ratings_df.columns else ratings_df
    rated_paths_for_source = {
        normalize_path(path_value)
        for path_value in rated_df["audio_path"].dropna().tolist()
    }

if developer_mode and audio_files:
    selected_audio_name = st.selectbox(
        "Select Any Audio (Developer)",
        options=[p.name for p in audio_files],
        index=st.session_state.audio_index,
        key=f"dev_audio_picker_{audio_source}"
    )
    selected_idx = next(i for i, p in enumerate(audio_files) if p.name == selected_audio_name)
    if selected_idx != st.session_state.audio_index:
        st.session_state.audio_index = selected_idx
        st.rerun()

# Evaluation
if audio_files:

    total_files = len(audio_files)

    # Prevent overflow
    if st.session_state.audio_index >= total_files:
        st.session_state.audio_index = total_files - 1

    current_file = audio_files[
        st.session_state.audio_index
    ]
    current_key = normalize_path(str(current_file))
    is_current_rated = current_key in rated_paths_for_source

    st.subheader(
        f"Audio {st.session_state.audio_index + 1} / {total_files}"
    )

    st.caption(f"Source: {audio_source} | Folder: {source_dir}")
    if is_current_rated:
        st.info("This audio already has a saved rating. You can update it.")
    st.audio(str(current_file))

    # Rating Section
    st.markdown("Rate Audio")

    col1, col2 = st.columns(2)

    with col1:
        naturalness = st.slider("Naturalness", 1, 5, 3)
        clarity = st.slider("Clarity", 1, 5, 3)

    with col2:
        pronunciation = st.slider("Pronunciation", 1, 5, 3)
        consistency = st.slider("Consistency", 1, 5, 3)


    b1, b2 = st.columns(2)

    with b1:
        submit_label = "Update Rating" if is_current_rated else "Submit Rating"
        if st.button(submit_label):

            data = {
                "model": audio_source,
                "audio": current_file.name,
                "audio_path": str(current_file),
                "naturalness": naturalness,
                "clarity": clarity,
                "pronunciation": pronunciation,
                "consistency": consistency
            }

            new_df = pd.DataFrame([data])

            if os.path.exists(RATINGS_FILE):
                old_df = load_ratings()
                if "audio_path" in old_df.columns and "model" in old_df.columns:
                    target_path = normalize_path(str(current_file))
                    old_df = old_df[
                        ~(
                            (old_df["model"] == audio_source)
                            & (old_df["audio_path"].astype(str).map(normalize_path) == target_path)
                        )
                    ]
                df = pd.concat([old_df, new_df],
                               ignore_index=True)
            else:
                df = new_df

            df.to_csv(RATINGS_FILE, index=False)

            st.success("Rating Saved!")

    with b2:
        if st.button("Next Audio"):

            if st.session_state.audio_index < total_files - 1:
                st.session_state.audio_index += 1
                st.rerun()
            else:
                st.warning("Last audio reached!")
else:
    st.warning(
        f"No audio files found for '{audio_source}'. "
        f"Expected one of: {', '.join(SOURCE_DIRS[audio_source])}"
    )

if (not developer_mode) and audio_files and rated_paths_for_source:
    st.markdown("---")
    st.subheader("Re-listen Rated Audio")
    rated_file_keys = sorted(
        [k for k in rated_paths_for_source if k in source_file_map],
        key=lambda x: source_file_map[x].name.lower()
    )
    if rated_file_keys:
        selected_rated_key = st.selectbox(
            "Rated files",
            options=rated_file_keys,
            format_func=lambda k: source_file_map[k].name,
            key=f"relisten_rated_{audio_source}"
        )
        st.audio(str(source_file_map[selected_rated_key]))

# Statistics Dashboard
st.markdown("---")
st.header("Evaluation Statistics")

if os.path.exists(RATINGS_FILE):

    df = load_ratings()

    numeric_cols = ["naturalness", "clarity", "pronunciation", "consistency"]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0.0

    total = len(df)
    unique = df["audio_path"].nunique() if "audio_path" in df.columns else df["audio"].nunique()

    avg_scores = df[numeric_cols].mean()
    overall = avg_scores.mean()

    c1, c2, c3 = st.columns(3)

    c1.metric("Ratings Submitted", total)
    c2.metric("Unique Audios Rated", unique)
    c3.metric("Overall Avg Score", round(overall, 2))

    st.subheader("Parameter Averages")
    st.dataframe(avg_scores.round(2))

    st.subheader("Model Comparison")
    model_scores = df.groupby("model")[numeric_cols].mean().round(2)
    model_scores["overall"] = model_scores.mean(axis=1).round(2)
    model_scores["ratings_count"] = df.groupby("model").size()
    st.dataframe(model_scores, width="stretch")

    if "sarvam" in model_scores.index and "elevenlabs" in model_scores.index:
        delta = (
            model_scores.loc["sarvam", numeric_cols + ["overall"]]
            - model_scores.loc["elevenlabs", numeric_cols + ["overall"]]
        ).round(2)
        delta_df = pd.DataFrame(delta).T
        delta_df.index = ["sarvam_minus_elevenlabs"]
        st.subheader("Direct Delta (Sarvam - ElevenLabs)")
        st.dataframe(delta_df, width="stretch")
