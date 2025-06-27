import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
from typing import List, Tuple

# Base URL for any "assets/..." paths in your CSV
MEDIA_PREFIX = "https://apptrack.chiraagtracker.com/"

st.set_page_config(layout="wide")
st.title("CHT Data Viewer")

# --- CSV Loader ---
@st.cache_data(show_spinner=False)
def load_csv(file) -> pd.DataFrame:
    return pd.read_csv(file)

uploaded = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded:
    df = load_csv(uploaded)
else:
    st.info("Please upload a CSV file to begin.")
    df = None

if df is not None:
    # Keep track of which row the user has picked
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None

    # --- 1) Global search + live suggestions ---
    search_query = st.text_input("Search for any value:")
    area = st.empty()

    if search_query:
        # Find up to 5 rows containing the query anywhere, case-insensitive
        mask = df.apply(
            lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1
        )
        matches = df[mask].head(5)

        if not matches.empty:
            # Build a radio list showing Extra2, CompanyName, ProspectName
            options = {
                idx: f"Extra2: {row['Extra2']} | Company: {row['CompanyName']} | Prospect: {row['ProspectName']}"
                for idx, row in matches.iterrows()
            }
            picked = area.radio(
                "Suggestions—pick a row to view details:",
                list(options.keys()),
                format_func=lambda i: f"Row {i} → {options[i]}",
                key="suggestions"
            )
            if picked is not None:
                st.session_state.selected_index = picked
        else:
            area.info("No matches found.")
    else:
        area.empty()

    # --- 2) Display selected row + fuzzy search + media preview ---
    if st.session_state.selected_index is not None:
        row = df.loc[st.session_state.selected_index]

        # **Your “Row 207” style horizontal display**
        st.subheader(f"Row {st.session_state.selected_index}")
        st.dataframe(row.to_frame().T, use_container_width=True)

        # --- 2a) Fuzzy search within this row ---
        inner = st.text_input("Search within this row:", key="inner")
        results_area = st.empty()
        if inner:
            def fuzzy_search(series: pd.Series, query: str, threshold: int = 60) -> List[Tuple[str, str, int]]:
                hits = []
                for col, val in series.items():
                    text = str(val)
                    score = max(
                        fuzz.token_set_ratio(query, col),
                        fuzz.token_set_ratio(query, text)
                    )
                    if score >= threshold:
                        hits.append((col, text, score))
                # sort by best match first
                hits.sort(key=lambda x: x[2], reverse=True)
                return hits

            hits = fuzzy_search(row, inner)
            if hits:
                for col, text, score in hits:
                    st.write(f"• **{col}**: {text}  _(score: {score})_")
            else:
                results_area.info("No close matches in this row.")
        else:
            results_area.empty()

        # --- 2b) Media detection & preview ---
        def detect_media(val: object) -> Tuple[str, str] | None:
            """
            If `val` is a URL or an assets/ path, return (kind, full_url),
            otherwise return None.
            """
            if not isinstance(val, str):
                return None

            url = None
            # Case 1: absolute URL
            if val.lower().startswith(("http://", "https://")):
                url = val
            # Case 2: relative assets path
            elif val.lower().startswith("assets/"):
                url = MEDIA_PREFIX.rstrip("/") + "/" + val

            if not url:
                return None

            # Grab extension (ignore query params)
            ext = url.split("?")[0].split(".")[-1].lower()

            # Classify by extension
            if ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
                return ("image", url)
            if ext in {"mp4", "webm", "mov", "avi"}:
                return ("video", url)
            if ext in {"mp3", "wav", "ogg", "m4a"}:
                return ("audio", url)
            if ext == "pdf":
                return ("pdf", url)
            # Anything else: fallback
            return ("other", url)

        media_items = []
        for cell in row:
            media = detect_media(cell)
            if media:
                media_items.append(media)

        if media_items:
            st.subheader("Media Preview")
            for kind, url in media_items:
                if kind == "image":
                    # Inline image
                    st.image(url, use_column_width=True)
                elif kind == "video":
                    # Inline video player
                    st.video(url)
                elif kind == "audio":
                    # Inline audio player
                    st.audio(url)
                elif kind == "pdf":
                    # Embed PDF in an iframe
                    st.components.v1.iframe(url, height=600)
                else:
                    # Fallback: show a download link
                    st.markdown(f"[Download file]({url})")
        else:
            st.info("No media found in this row.")
