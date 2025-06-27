import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("CSV Duplicate Analyzer & Cleaner")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Data Preview:")
    st.dataframe(df.head(20), use_container_width=True)
    st.subheader("Duplicate Analysis")
    # Show duplicate summary for all columns
    dup_counts = df.duplicated().sum()
    st.write(f"Total duplicate rows (all columns): {dup_counts}")
    st.write("---")
    st.write("Column-wise duplicate counts:")
    col1, col2 = st.columns(2)
    with col1:
        for col in df.columns:
            st.write(f"{col}: {df.duplicated(subset=[col]).sum()} duplicates")
    with col2:
        st.write("Select columns to check for duplicates:")
        selected_cols = st.multiselect("Columns", options=df.columns.tolist())
        if selected_cols:
            st.write(f"Duplicate rows for selected columns: {df.duplicated(subset=selected_cols).sum()}")
            st.dataframe(df[df.duplicated(subset=selected_cols, keep=False)], use_container_width=True)
    st.write("---")
    st.subheader("Duplicate Cleanup")
    if selected_cols:
        keep_option = st.radio("When removing duplicates, keep:", ["first", "last", "none (remove all)"])
        if st.button("Remove Duplicates"):
            if keep_option == "none (remove all)":
                cleaned_df = df[~df.duplicated(subset=selected_cols, keep=False)]
            else:
                cleaned_df = df.drop_duplicates(subset=selected_cols, keep=keep_option)
            st.write(f"Rows after duplicate removal: {len(cleaned_df)}")
            st.dataframe(cleaned_df.head(20), use_container_width=True)
            csv = cleaned_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Cleaned CSV", csv, "cleaned_data.csv", "text/csv")
else:
    st.info("Please upload a CSV file to begin.")
