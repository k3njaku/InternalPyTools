import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

MEDIA_PREFIX = "https://apptrack.chiraagtracker.com/assets/"

st.set_page_config(layout="wide")
st.title("CSV Media Explorer")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = None

selected_row = None
if df is not None:
    st.subheader("Search Dataset")
    query = st.text_input("Search for any value:", key="main_search")
    suggestions_container = st.container()
    if query:
        mask = df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)
        suggestions = df[mask].head(10)
        options = [f"{i}: " + " | ".join(str(x) for x in suggestions.loc[i].astype(str).values[:3]) for i in suggestions.index]
        choice = suggestions_container.selectbox("Suggestions", options, index=0 if options else None)
        if choice:
            selected_row = int(choice.split(":" )[0])
    st.divider()

if df is not None and selected_row is not None:
    row = df.loc[selected_row]
    st.subheader(f"Row {selected_row} Details")
    st.table(row)

    search_within = st.text_input("Search within this row:", key="row_search")
    if search_within:
        results = []
        for col, val in row.items():
            score = fuzz.partial_ratio(str(val).lower(), search_within.lower())
            if score >= 70:
                results.append((score, col, val))
        for _, col, val in sorted(results, reverse=True):
            st.write(f"**{col}**: {val}")
    st.divider()

    st.subheader("Media Preview")
    media_found = False
    for col, val in row.items():
        if isinstance(val, str):
            lower = val.lower()
            url = val if val.startswith("http") else MEDIA_PREFIX + val.lstrip("/")
            if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                st.image(url, caption=col)
                media_found = True
            elif lower.endswith((".mp4", ".webm", ".ogg")):
                st.video(url)
                media_found = True
            elif lower.endswith((".mp3", ".wav", ".m4a", ".ogg")):
                st.audio(url)
                media_found = True
            elif lower.endswith(".pdf"):
                st.markdown(f'<embed src="{url}" type="application/pdf" width="700" height="500">', unsafe_allow_html=True)
                media_found = True
    if not media_found:
        st.info("No media found in this row.")
