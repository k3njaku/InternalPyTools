import streamlit as st
import pandas as pd
import re
import difflib

st.set_page_config(layout="wide")
st.title("CHT Data Viewer")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

@st.cache_data
def load_and_transform_csv(file):
    df = pd.read_csv(file)
    # Transform all partial asset URLs
    def transform_url(val):
        if isinstance(val, str) and val.startswith("assets/"):
            return "https://apptrack.chiraagtracker.com/" + val
        return val
    return df.applymap(transform_url)

def search_suggestions(df, query):
    suggestions = []
    for idx, row in df.iterrows():
        for col in df.columns:
            if pd.notna(row[col]) and query.lower() in str(row[col]).lower():
                suggestions.append({
                    "row": idx,
                    "Extra2": row.get("Extra2", ""),
                    "CompanyName": row.get("CompanyName", ""),
                    "ProspectName": row.get("ProspectName", ""),
                    "value": row[col],
                    "column": col
                })
                break
    return suggestions

def find_media_links(row):
    media_links = []
    for col, val in row.items():
        if isinstance(val, str) and val.startswith("https://apptrack.chiraagtracker.com/assets/"):
            media_links.append((col, val))
    return media_links

def preview_media(url):
    if re.search(r"\\.(jpg|jpeg|png|gif|bmp|webp)$", url, re.IGNORECASE):
        st.image(url, use_column_width=True)
    elif re.search(r"\\.(mp4|webm|ogg|mov)$", url, re.IGNORECASE):
        st.video(url)
    elif re.search(r"\\.(mp3|wav|aac|m4a|flac)$", url, re.IGNORECASE):
        st.audio(url)
    elif re.search(r"\\.(pdf)$", url, re.IGNORECASE):
        st.markdown(f"[View PDF]({url})")
        st.components.v1.iframe(url, height=600)
    else:
        st.markdown(f"[Download/View]({url})")

# --- Real-time search suggestions ---
if uploaded_file:
    df = load_and_transform_csv(uploaded_file)
    st.session_state["df"] = df
    st.subheader("Search Data")
    search_query = st.text_input("Search for any value:", key="main_search")
    suggestions = []
    selected_row = None
    if search_query:
        # Real-time suggestions (up to 10 unique values)
        suggestions = search_suggestions(df, search_query)
        options = [f"Row {s['row']} | Extra2: {s['Extra2']} | CompanyName: {s['CompanyName']} | ProspectName: {s['ProspectName']}" for s in suggestions][:10]
        if options:
            selected_suggestion = st.selectbox("Suggestions:", ["(Type to search)"] + options, key="suggestion_box")
            if selected_suggestion != "(Type to search)":
                selected_idx = options.index(selected_suggestion)
                selected_row = suggestions[selected_idx]["row"]
        else:
            st.info("No matches found.")
    if selected_row is not None:
        row_data = df.loc[selected_row]
        st.markdown("---")
        st.subheader(f"Row {selected_row} Details (Transposed)")
        # Transposed view
        transposed = pd.DataFrame(row_data).reset_index()
        transposed.columns = ["Header", "Value"]
        st.dataframe(transposed, use_container_width=True)
        # Fuzzy search within row
        row_search = st.text_input("Search within this row:", key="row_search")
        if row_search:
            # Use difflib for fuzzy matching
            matches = []
            for idx, val in enumerate(transposed["Value"].astype(str)):
                if difflib.SequenceMatcher(None, row_search.lower(), val.lower()).ratio() > 0.5:
                    matches.append(transposed.iloc[idx])
            if matches:
                st.write("Matches:")
                st.dataframe(pd.DataFrame(matches), use_container_width=True)
            else:
                st.info("No fuzzy matches in this row.")
        # Media view
        st.markdown("---")
        st.subheader("Media in this Row")
        media_links = find_media_links(row_data)
        if media_links:
            for col, url in media_links:
                st.write(f"{col}: {url}")
                preview_media(url)
        else:
            st.info("No media links found in this row.")
else:
    st.info("Please upload a CSV file to begin.")
