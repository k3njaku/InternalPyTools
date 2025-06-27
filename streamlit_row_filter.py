import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("CSV Row Filter & Keeper")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.session_state["df"] = df
    st.write("Data Preview:")
    st.dataframe(df.head(20), use_container_width=True)
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_object_dtype(df[col])]
    st.sidebar.header("Filter Rows by Date Range")
    date_col = st.sidebar.selectbox("Select date column", date_cols)
    if date_col:
        # Try to parse the column as datetime
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        start_date, end_date = st.sidebar.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        action = st.sidebar.radio("Action", ["Keep rows in range", "Delete rows in range"])
        if st.sidebar.button("Apply Filter"):
            mask = df[date_col].between(pd.to_datetime(start_date), pd.to_datetime(end_date))
            if action == "Keep rows in range":
                result_df = df[mask]
            else:
                result_df = df[~mask]
            st.write(f"Filtered Data ({len(result_df)} rows):")
            st.dataframe(result_df.head(20), use_container_width=True)
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Resulting CSV", csv, "filtered_data.csv", "text/csv")
else:
    st.info("Please upload a CSV file to begin.")
