import streamlit as st
import pandas as pd
import base64
import requests
import importlib
from rapidfuzz import fuzz
from typing import Tuple

# Base URL for any "assets/..." paths
MEDIA_PREFIX = "https://apptrack.chiraagtracker.com/"

st.set_page_config(layout="wide")
st.title("CHT Data Viewer — Full Media & PDF Support")

# --- CSV Loader ---
@st.cache_data(show_spinner=False)
def load_csv(file) -> pd.DataFrame:
    return pd.read_csv(file)

# --- PDF display helper ---
def show_pdf(source: str | bytes, height: int = 700):
    """
    Display a PDF via:
      1) streamlit-pdf-viewer (PDF.js) if installed
      2) base64 <embed> (for bytes <2 MB)
      3) plain <iframe> (for public URLs)
    """
    # 1. PDF.js component
    if importlib.util.find_spec("streamlit_pdf_viewer"):
        from streamlit_pdf_viewer import pdf_viewer  # type: ignore
        pdf_bytes = source if isinstance(source, bytes) else requests.get(source).content
        pdf_viewer(pdf_bytes, width="100%", height=height)
        return

    # 2. base64 embed (Chrome caps data URIs ≈2 MB)
    if isinstance(source, bytes) and len(source) < 2_000_000:
        b64 = base64.b64encode(source).decode()
        html = (
            f'<embed src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="{height}px" type="application/pdf" />'
        )
        st.components.v1.html(html, height=height)
        return

    # 3. iframe fallback
    if isinstance(source, str):
        html = (
            f'<iframe src="{source}#toolbar=0" width="100%" '
            f'height="{height}px" type="application/pdf" style="border:none;"></iframe>'
        )
        st.components.v1.html(html, height=height)
    else:
        st.error("Cannot preview PDF (install streamlit-pdf-viewer or use a smaller file).")

# --- Media detection helper ---
def detect_media(val: object) -> Tuple[str, str] | None:
    """
    If val is an image/video/audio/pdf URL or an assets/ path,
    returns (kind, full_url); else None.
    """
    if not isinstance(val, str):
        return None

    url = None
    lower = val.lower()
    if lower.startswith(("http://", "https://")):
        url = val
    elif lower.startswith("assets/"):
        url = MEDIA_PREFIX.rstrip("/") + "/" + val

    if not url:
        return None

    ext = url.split("?")[0].split(".")[-1].lower()
    if ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
        return "image", url
    if ext in {"mp4", "webm", "mov", "avi"}:
        return "video", url
    if ext in {"mp3", "wav", "ogg", "m4a"}:
        return "audio", url
    if ext == "pdf":
        return "pdf", url
    return "other", url

# --- Fuzzy search helper ---
def fuzzy_hits(series: pd.Series, query: str, thresh: int = 60):
    hits = []
    for col, val in series.items():
        text = str(val)
        score = max(fuzz.token_set_ratio(query, col),
                    fuzz.token_set_ratio(query, text))
        if score >= thresh:
            hits.append((col, text, score))
    return sorted(hits, key=lambda x: x[2], reverse=True)

# --- Main App ---
uploaded = st.file_uploader("Upload your CSV file", type=["csv"])
df = load_csv(uploaded) if uploaded else None

if df is not None:
    # Persist selected row index
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None

    # 1) Global search + live suggestions
    search_query = st.text_input("Search for any value:")
    suggestions_box = st.empty()
    if search_query:
        mask = df.apply(
            lambda r: r.astype(str).str.contains(search_query, case=False, na=False).any(),
            axis=1
        )
        matches = df[mask].head(5)
        if not matches.empty:
            options = {
                idx: f"Extra2={row['Extra2']} | Company={row['CompanyName']} | Prospect={row['ProspectName']}"
                for idx, row in matches.iterrows()
            }
            choice = suggestions_box.radio(
                "Suggestions—select a row:",
                list(options.keys()),
                format_func=lambda i: f"Row {i}: {options[i]}"
            )
            st.session_state.selected_index = choice
        else:
            suggestions_box.info("No matches found.")
    else:
        suggestions_box.empty()

    # 2) Display selected row + fuzzy search + media preview
    sel = st.session_state.selected_index
    if sel is not None:
        row = df.loc[sel]
        st.subheader(f"Row {sel}")
        st.dataframe(row.to_frame().T, use_container_width=True)

        # 2a) Fuzzy search within this row
        inner_q = st.text_input("Search within this row:", key="inner")
        if inner_q:
            for col, text, score in fuzzy_hits(row, inner_q):
                st.write(f"• **{col}**: {text} _(score {score})_")

        # 2b) Media & PDF preview
        media_items = [m for m in (detect_media(v) for v in row.values) if m]
        if media_items:
            st.subheader("Media Preview")
            for kind, url in media_items:
                if kind == "image":
                    st.image(url, use_column_width=True)
                elif kind == "video":
                    st.video(url)
                elif kind == "audio":
                    st.audio(url)
                elif kind == "pdf":
                    with st.spinner("Loading PDF…"):
                        show_pdf(url)
                else:
                    st.markdown(f"[Download file]({url})")
        else:
            st.info("No media found in this row.")
else:
    st.info("Please upload a CSV file to begin.")
