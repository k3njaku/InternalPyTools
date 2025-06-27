import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
from typing import List, Tuple

MEDIA_PREFIX = "https://apptrack.chiraagtracker.com/"

st.set_page_config(layout="wide")
st.title("CSV Media Explorer")

# Utility to load csv file
@st.cache_data(show_spinner=False)
def load_csv(file) -> pd.DataFrame:
    return pd.read_csv(file)

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    df = load_csv(uploaded)
else:
    st.info("Please upload a CSV file to begin.")
    df = None

if df is not None:
    if 'selected_index' not in st.session_state:
        st.session_state.selected_index = None

    search_query = st.text_input("Search for any value:")
    suggestions_area = st.empty()

    if search_query:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)
        matches = df[mask].head(5)
        if not matches.empty:
            options = {idx: ", ".join(str(row[col]) for col in df.columns[:3]) for idx, row in matches.iterrows()}
            chosen = suggestions_area.radio("Suggestions", list(options.keys()), format_func=lambda x: f"Row {x}: {options[x]}", key="suggestions")
            if chosen is not None:
                st.session_state.selected_index = chosen
        else:
            suggestions_area.info("No matches found.")
    else:
        suggestions_area.empty()

    if st.session_state.selected_index is not None:
        row = df.loc[st.session_state.selected_index]
        st.subheader(f"Row {st.session_state.selected_index}")
        st.write(row.to_frame().T)

        inner_query = st.text_input("Search within this row:", key="inner")
        results_area = st.empty()
        if inner_query:
            def fuzzy(row_series, query, threshold=60) -> List[Tuple[str, str, int]]:
                res = []
                for col, val in row_series.items():
                    val_str = str(val)
                    score = max(fuzz.token_set_ratio(query, col), fuzz.token_set_ratio(query, val_str))
                    if score >= threshold:
                        res.append((col, val_str, score))
                res.sort(key=lambda x: x[2], reverse=True)
                return res
            results = fuzzy(row, inner_query)
            if results:
                for col, val, score in results:
                    st.write(f"{col}: {val} ({score})")
            else:
                results_area.info("No close matches in this row.")
        else:
            results_area.empty()

        def detect_media(value: str):
            if not isinstance(value, str):
                return None
            url = None
            if value.lower().startswith("http://") or value.lower().startswith("https://"):
                url = value
            elif value.lower().startswith("assets/"):
                url = MEDIA_PREFIX.rstrip('/') + '/' + value
            if not url:
                return None
            ext = url.split('?')[0].split('.')[-1].lower()
            if ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
                return ("image", url)
            if ext in {"mp4", "webm", "mov", "avi"}:
                return ("video", url)
            if ext in {"mp3", "wav", "ogg", "m4a"}:
                return ("audio", url)
            if ext == "pdf":
                return ("pdf", url)
            return ("other", url)

        media_items = []
        for val in row.values:
            media = detect_media(val)
            if media:
                media_items.append(media)

        if media_items:
            st.subheader("Media Preview")
            for kind, url in media_items:
                if kind == "image":
                    st.image(url)
                elif kind == "video":
                    st.video(url)
                elif kind == "audio":
                    st.audio(url)
                elif kind == "pdf":
                    st.components.v1.iframe(url, height=600)
                else:
                    st.markdown(f"[Download file]({url})")
        else:
            st.info("No media found in this row.")
