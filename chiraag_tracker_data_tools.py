import streamlit as st
import pandas as pd
import requests
import json
from datetime import date

# --- Configuration ---
BASE_URL = "https://apptrack.chiraagtracker.com/ajax"
DEFAULT_PARAMS = {
    "Option": "FetchFilteredAppointments",
    "Id": "144", # Assuming this is static, adjust if needed
    "OID": "1",  # Assuming this is static
    "UserId": "0",
    "DeptId": "0",
    "URUserRole": "Admin",
    "QAStatus": "0",
    "SchOnStartDate": "00-00-0000",
    "SchOnEndDate": "00-00-0000",
    "SchForStartDate": "00-00-0000",
    "SchForEndDate": "00-00-0000"
}

# --- Helper Functions (adapted from importData.py) ---
def process_fetched_data(data_list):
    """
    Processes the raw JSON data list into a pandas DataFrame.
    Determines headers dynamically and flattens records.
    """
    if not data_list or not isinstance(data_list, list):
        return pd.DataFrame(), [] # Return empty DataFrame and headers if data is not as expected

    valid_records = [rec for rec in data_list if isinstance(rec, list) and len(rec) > 0 and isinstance(rec[0], dict)]

    if not valid_records:
        st.warning("No processable records found in the fetched data.")
        return pd.DataFrame(), []

    # Determine headers for the JSON object and additional fields
    json_keys = set()
    for record in valid_records:
        json_keys.update(record[0].keys())

    sorted_json_keys = sorted(list(json_keys))
    
    max_record_len = 0
    if valid_records: # Ensure valid_records is not empty before calling max
        max_record_len = max(len(record) for record in valid_records)
    # else: # This case is now handled by the early return if not valid_records
    #     return pd.DataFrame(), sorted_json_keys


    additional_field_count = max(0, max_record_len - 1) # max_record_len includes the dict part
    additional_headers = [f'Extra{i}' for i in range(1, additional_field_count + 1)]
    headers = sorted_json_keys + additional_headers

    flattened_rows = []
    for record in data_list:
        if not (isinstance(record, list) and len(record) > 0 and isinstance(record[0], dict)):
            continue # Skip records already warned about

        json_part = record[0]
        row_values = [json_part.get(key, '') for key in sorted_json_keys]
        
        additional_parts = record[1:] if len(record) > 1 else []
        # Ensure additional_parts has the correct length for zipping with additional_headers
        # This padding logic needs to be careful if additional_field_count is 0
        padded_additional_parts = list(additional_parts) + [''] * (additional_field_count - len(additional_parts))
        row_values.extend(padded_additional_parts)
        flattened_rows.append(row_values)

    return pd.DataFrame(flattened_rows, columns=headers), headers

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("AJAX Data Importer for Chiraag Tracker")

# --- Initialize Session State ---
if 'fetched_df' not in st.session_state:
    st.session_state.fetched_df = None
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'last_success' not in st.session_state:
    st.session_state.last_success = None

# --- User Inputs ---
st.sidebar.header("Filter Parameters")
start_date_input = st.sidebar.date_input("Select Start Date", date.today())
end_date_input = st.sidebar.date_input("Select End Date", date.today())

if st.sidebar.button("Fetch Data"):
    st.session_state.fetched_df = None # Reset previous data
    st.session_state.last_error = None
    st.session_state.last_success = None

    if start_date_input > end_date_input:
        st.session_state.last_error = "Error: Start Date cannot be after End Date."
    else:
        # Format dates as DD-MM-YYYY
        start_date_str = start_date_input.strftime("%d-%m-%Y")
        end_date_str = end_date_input.strftime("%d-%m-%Y")

        # Construct dynamic params
        dynamic_params = DEFAULT_PARAMS.copy()
        dynamic_params["StartDate"] = start_date_str
        dynamic_params["EndDate"] = end_date_str

        try:
            st.info(f"Fetching data for StartDate: {start_date_str}, EndDate: {end_date_str}...")
            response = requests.get(BASE_URL, params=dynamic_params)
            response.raise_for_status()  # Raise an error for HTTP errors (4xx or 5xx)
            
            raw_data = response.json()
            
            if raw_data:
                processed_df, _ = process_fetched_data(raw_data)
                if not processed_df.empty:
                    st.session_state.fetched_df = processed_df
                    st.session_state.last_success = f"Successfully fetched {len(processed_df)} records."
                elif not st.session_state.last_error: # if process_fetched_data found no valid data but didn't set an error
                    st.session_state.last_error = "Data fetched, but no processable records found or all records had unexpected format."

            else:
                st.session_state.last_error = "No data returned from the API."

        except requests.exceptions.Timeout:
            st.session_state.last_error = "Error: The request to the server timed out."
        except requests.exceptions.ConnectionError:
            st.session_state.last_error = "Error: Could not connect to the server. Please check your internet connection or the server status."
        except requests.exceptions.HTTPError as e:
            st.session_state.last_error = f"HTTP Error: {e.response.status_code} - {e.response.reason}. Response: {e.response.text[:200]}..."
        except json.JSONDecodeError:
            st.session_state.last_error = "Error: Could not parse the JSON response from the server. The data might not be in valid JSON format."
        except Exception as e:
            st.session_state.last_error = f"An unexpected error occurred: {str(e)}"

# --- Display Messages ---
if st.session_state.last_error:
    st.error(st.session_state.last_error)
if st.session_state.last_success:
    st.success(st.session_state.last_success)

# --- Display Data and Download ---
if st.session_state.fetched_df is not None and not st.session_state.fetched_df.empty:
    st.subheader("Fetched Data Preview")
    st.dataframe(st.session_state.fetched_df.head(20)) # Show more rows in preview

    st.subheader("Download Data")
    
    @st.cache_data # Cache the conversion to CSV
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8')

    csv_data = convert_df_to_csv(st.session_state.fetched_df)
    
    download_filename = f"chiraag_tracker_data_{start_date_input.strftime('%Y%m%d')}_to_{end_date_input.strftime('%Y%m%d')}.csv"
    
    st.download_button(
        label="Download as CSV",
        data=csv_data,
        file_name=download_filename,
        mime="text/csv"
    )
elif st.session_state.fetched_df is not None and st.session_state.fetched_df.empty and not st.session_state.last_error:
    st.info("No data to display based on the current filters or API response.")