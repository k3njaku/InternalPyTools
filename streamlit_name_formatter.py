import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("Name Formatter & Converter")

uploaded_file = st.file_uploader("Upload your CSV file (with name columns)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Data Preview:")
    st.dataframe(df.head(20), use_container_width=True)
    st.subheader("Name Formatting Options")
    # Guess name columns
    name_cols = [col for col in df.columns if 'name' in col.lower() or 'first' in col.lower() or 'last' in col.lower()]
    first_col = st.selectbox("First Name column", name_cols, index=0 if name_cols else None)
    last_col = st.selectbox("Last Name column", name_cols, index=1 if len(name_cols) > 1 else 0)
    action = st.radio("Action", ["Concatenate to Full Name", "Split Full Name", "Capitalize Names", "Smart Split (using LinkedIn)"])
    if action == "Concatenate to Full Name":
        new_col = st.text_input("New column name for full name", value="FullName")
        if st.button("Create Full Name"):
            df[new_col] = df[first_col].astype(str).str.strip() + " " + df[last_col].astype(str).str.strip()
            st.dataframe(df[[first_col, last_col, new_col]].head(20), use_container_width=True)
    elif action == "Split Full Name":
        full_col = st.selectbox("Full Name column", name_cols, index=0 if name_cols else None)
        if st.button("Split Names"):
            df['FirstName'] = df[full_col].astype(str).str.split().str[0]
            df['LastName'] = df[full_col].astype(str).str.split().str[-1]
            st.dataframe(df[[full_col, 'FirstName', 'LastName']].head(20), use_container_width=True)
    elif action == "Capitalize Names":
        col_to_cap = st.selectbox("Column to capitalize", name_cols, index=0 if name_cols else None)
        if st.button("Capitalize"):
            df[col_to_cap] = df[col_to_cap].astype(str).str.title()
            st.dataframe(df[[col_to_cap]].head(20), use_container_width=True)
    elif action == "Smart Split (using LinkedIn)":
        name_col = st.selectbox("Column with full or first names", name_cols, index=0 if name_cols else None, key="smart_name_col")
        linkedin_col = st.selectbox("LinkedIn URL column (optional)", [col for col in df.columns if 'linkedin' in col.lower()] + [None], index=0, key="smart_linkedin_col")
        def smart_split(row):
            name = str(row[name_col]).strip()
            # Try to split by space
            parts = name.split()
            
            def clean_last_name(last_name):
                # Keep apostrophes and hyphens if they're between letters (like O'Brien or Smith-Jones)
                # First, preserve valid name special characters
                last_name = re.sub(r"([a-zA-Z])'([a-zA-Z])", r"\1_APOS_\2", last_name)
                last_name = re.sub(r"([a-zA-Z])-([a-zA-Z])", r"\1_HYPH_\2", last_name)
                # Remove all non-alphabetic characters
                last_name = ''.join(c for c in last_name if c.isalpha() or c == '_')
                # Restore special characters
                last_name = last_name.replace('_APOS_', "'").replace('_HYPH_', '-')
                return last_name.title()

            # If only one part, try to extract from LinkedIn URL
            if len(parts) == 1 and linkedin_col and pd.notna(row[linkedin_col]):
                # LinkedIn URLs are like .../in/firstname-lastname or .../in/firstname.lastname
                match = re.search(r'/in/([a-zA-Z0-9\-\.]+)', str(row[linkedin_col]))
                if match:
                    handle = match.group(1).replace('.', ' ').replace('-', ' ')
                    handle_parts = handle.split()
                    if len(handle_parts) >= 2:
                        return pd.Series({
                            'FirstName': handle_parts[0].title(),
                            'LastName': clean_last_name(handle_parts[-1])
                        })
            # Fallback: first word is first name, last word is last name
            return pd.Series({
                'FirstName': parts[0].title() if parts else '',
                'LastName': clean_last_name(parts[-1]) if len(parts) > 1 else ''
            })
        
        if st.button("Smart Split Names"):
            split_names = df.apply(smart_split, axis=1)
            df['FirstName'] = split_names['FirstName']
            df['LastName'] = split_names['LastName']
            st.write("Name Split Results (first 20 rows):")
            st.dataframe(df[[name_col, 'FirstName', 'LastName']].head(20), use_container_width=True)
            
            # Add a summary of changes made
            total_processed = len(df)
            empty_last_names = df['LastName'].isna().sum() + (df['LastName'] == '').sum()
            st.info(f"""
            Processing Summary:
            - Total rows processed: {total_processed}
            - Rows with empty last names: {empty_last_names}
            """)
    st.subheader("Download Modified CSV")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "formatted_names.csv", "text/csv")
else:
    st.info("Please upload a CSV file to begin.")
