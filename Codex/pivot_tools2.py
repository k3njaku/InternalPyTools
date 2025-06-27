import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import datetime

st.set_page_config(layout="wide")
st.title("Interactive Multi-Pivot Table Creator")

# --- Initialize Session State ---
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'multi_pivots' not in st.session_state:
    st.session_state.multi_pivots = []  # List of dicts, each dict is a pivot config
if 'active_pivot' not in st.session_state:
    st.session_state.active_pivot = 0  # Index of currently selected pivot

# --- File Upload ---
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    if st.session_state.uploaded_file_name != uploaded_file.name:
        try:
            df_temp = pd.read_csv(uploaded_file)
            # Clean invalid date values in all columns
            for col in df_temp.columns:
                if df_temp[col].dtype == object:
                    df_temp[col] = df_temp[col].replace('0000-00-00', pd.NA)
                    try:
                        df_temp[col] = pd.to_datetime(df_temp[col], errors='ignore')
                    except Exception:
                        pass
            st.session_state.df = df_temp
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.multi_pivots = []
            st.session_state.active_pivot = 0
        except Exception as e:
            st.session_state.df = None
            st.session_state.uploaded_file_name = None
            st.sidebar.error(f"Error loading CSV: {e}")
else:
    if st.session_state.df is not None and uploaded_file is None:
        st.session_state.df = None
        st.session_state.uploaded_file_name = None
        st.session_state.multi_pivots = []
        st.session_state.active_pivot = 0

def serialize_dates(obj):
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(v) for v in obj]
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return obj

# --- Multi-Pivot Management ---
SAVED_VIEWS_FILE = 'saved_pivot_views.json'

def default_pivot_config(df):
    cols = df.columns.tolist() if df is not None else []
    return {
        'name': f"Pivot {len(st.session_state.multi_pivots)+1}",
        'index_cols': [],
        'column_cols': [],
        'value_agg_list': [],
        'filters': [],
        'fill_value_enabled': False,
        'custom_fill_value': None,
        'margins_enabled': False,
        'margins_name': "All_Totals",
        'pivot_df': None,
        'last_error': None,
        'last_success': None,
        'generated_code': None
    }

def save_views():
    with open(SAVED_VIEWS_FILE, 'w') as f:
        json.dump([serialize_dates({
            k: v for k, v in p.items() if k != 'pivot_df'  # Don't save DataFrames
        }) for p in st.session_state.multi_pivots], f)

def load_views():
    try:
        with open(SAVED_VIEWS_FILE, 'r') as f:
            loaded = json.load(f)
            # Restore all configs except DataFrames
            for p in loaded:
                p['pivot_df'] = None
            st.session_state.multi_pivots = loaded
            st.session_state.active_pivot = 0
    except Exception:
        pass

if st.sidebar.button("Save All Views"):
    save_views()
if st.sidebar.button("Load Saved Views"):
    load_views()

if st.session_state.df is not None:
    # Add/Remove Pivot Tabs
    st.sidebar.markdown("## Manage Pivots")
    if st.sidebar.button("Add New Pivot"):
        st.session_state.multi_pivots.append(default_pivot_config(st.session_state.df))
        st.session_state.active_pivot = len(st.session_state.multi_pivots) - 1
    if st.session_state.multi_pivots:
        pivot_names = [p['name'] for p in st.session_state.multi_pivots]
        st.session_state.active_pivot = st.sidebar.selectbox(
            "Select Pivot", options=list(range(len(pivot_names))), format_func=lambda i: pivot_names[i],
            index=st.session_state.active_pivot if st.session_state.active_pivot < len(pivot_names) else 0
        )
        if st.sidebar.button("Remove Selected Pivot") and len(st.session_state.multi_pivots) > 0:
            st.session_state.multi_pivots.pop(st.session_state.active_pivot)
            st.session_state.active_pivot = max(0, st.session_state.active_pivot - 1)

# --- Pivot Table Configuration and Display ---
# … (rest of the very long script continues unchanged)
