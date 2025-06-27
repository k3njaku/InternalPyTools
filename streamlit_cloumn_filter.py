import streamlit as st
import pandas as pd
import io # Required for download button in some cases

st.set_page_config(layout="wide") # Use wide layout for more space

st.title("Interactive CSV Column Selector")

# Initialize session state variables if they don't exist
if 'dataframe' not in st.session_state:
    st.session_state.dataframe = None
if 'original_dataframe' not in st.session_state: # To store the very first loaded DF for reset
    st.session_state.original_dataframe = None
if 'original_columns' not in st.session_state: # To store columns of the very first loaded DF
    st.session_state.original_columns = []
if 'current_columns' not in st.session_state: # Columns of the currently displayed/modified DF
    st.session_state.current_columns = []
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = "modified_data.csv"
if 'message' not in st.session_state:
    st.session_state.message = ""
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""


uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Check if this is a new file upload or if we're working with an existing one
    # This simple check might need refinement for more complex scenarios
    if st.session_state.dataframe is None or st.session_state.uploaded_file_name != uploaded_file.name:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.dataframe = df.copy() # Work with a copy
            st.session_state.original_dataframe = df.copy() # Store for reset
            st.session_state.original_columns = df.columns.tolist()
            st.session_state.current_columns = df.columns.tolist()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.message = f"Successfully loaded '{uploaded_file.name}' with {len(st.session_state.current_columns)} columns."
            st.session_state.error_message = ""
            st.success(st.session_state.message)
        except Exception as e:
            st.session_state.dataframe = None
            st.session_state.original_dataframe = None
            st.session_state.original_columns = []
            st.session_state.current_columns = []
            st.session_state.error_message = f"Error loading file: {e}"
            st.session_state.message = ""
            st.error(st.session_state.error_message)
            # Clear the uploader if there's an error to allow re-upload
            # This is a bit of a hack, Streamlit doesn't have a direct "clear uploader" API
            # uploaded_file = None # This won't work as expected due to rerun
else:
    # If no file is uploaded, and there was one before, reset state
    if st.session_state.dataframe is not None and uploaded_file is None: # Heuristic for clearing
        st.session_state.dataframe = None
        st.session_state.original_dataframe = None
        st.session_state.original_columns = []
        st.session_state.current_columns = []
        st.session_state.message = "Please upload a CSV file."
        st.session_state.error_message = ""


if st.session_state.dataframe is not None:
    st.subheader("Column Management")

    # Use two columns for better layout
    col1, col2 = st.columns(2)

    with col1:
        st.write("Available Columns:")
        # The multiselect default should be all current columns
        selected_columns_for_action = st.multiselect(
            "Select columns to keep or remove:",
            options=st.session_state.current_columns,
            default=st.session_state.current_columns # Default to all current columns
        )

    with col2:
        st.write("Actions:")
        if st.button("Keep Selected Columns"):
            if not selected_columns_for_action:
                st.session_state.error_message = "No columns selected to keep."
                st.session_state.message = ""
            elif len(selected_columns_for_action) == len(st.session_state.current_columns) and \
                 all(col in st.session_state.current_columns for col in selected_columns_for_action):
                st.session_state.message = "All current columns are selected. No change made."
                st.session_state.error_message = ""
            else:
                try:
                    st.session_state.dataframe = st.session_state.dataframe[selected_columns_for_action]
                    st.session_state.current_columns = st.session_state.dataframe.columns.tolist()
                    st.session_state.message = f"Kept {len(st.session_state.current_columns)} columns."
                    st.session_state.error_message = ""
                except Exception as e:
                    st.session_state.error_message = f"Error keeping columns: {e}"
                    st.session_state.message = ""


        if st.button("Remove Selected Columns"):
            if not selected_columns_for_action:
                st.session_state.error_message = "No columns selected to remove."
                st.session_state.message = ""
            else:
                cols_to_remove = [col for col in selected_columns_for_action if col in st.session_state.current_columns]
                if not cols_to_remove:
                    st.session_state.error_message = "Selected columns for removal not found in current dataset."
                    st.session_state.message = ""
                else:
                    try:
                        st.session_state.dataframe = st.session_state.dataframe.drop(columns=cols_to_remove)
                        st.session_state.current_columns = st.session_state.dataframe.columns.tolist()
                        st.session_state.message = f"Removed {len(cols_to_remove)} columns. Remaining: {len(st.session_state.current_columns)}."
                        st.session_state.error_message = ""
                    except Exception as e:
                        st.session_state.error_message = f"Error removing columns: {e}"
                        st.session_state.message = ""

        if st.button("Reset to Original Columns"):
            if st.session_state.original_dataframe is not None:
                st.session_state.dataframe = st.session_state.original_dataframe.copy()
                st.session_state.current_columns = st.session_state.original_columns[:] # Use slicing for a new list copy
                st.session_state.message = "Columns reset to original state."
                st.session_state.error_message = ""
            else:
                st.session_state.error_message = "No original data to reset to."
                st.session_state.message = ""

    # Display status messages
    if st.session_state.message:
        st.info(st.session_state.message)
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    st.subheader("Data Preview (First 10 rows)")
    st.dataframe(st.session_state.dataframe.head(10))

    st.subheader("Download Modified CSV")

    # Convert DataFrame to CSV string for download
    @st.cache_data # Cache the conversion
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8')

    csv_to_download = convert_df_to_csv(st.session_state.dataframe)

    st.download_button(
        label="Download data as CSV",
        data=csv_to_download,
        file_name=f"modified_{st.session_state.uploaded_file_name}",
        mime='text/csv',
    )
elif st.session_state.message: # Show initial message if no df but message exists
    st.info(st.session_state.message)