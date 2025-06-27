import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import datetime

st.set_page_config(layout="wide")
st.title("Interactive Multi-Pivot Table Creator v2")

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

# --- Show All Data Rows ---
if st.session_state.df is not None:
    st.subheader("All Data Rows")
    st.dataframe(st.session_state.df, use_container_width=True)
    # Download all data rows as CSV
    csv_all_data = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download All Data Rows as CSV",
        data=csv_all_data,
        file_name="all_data_rows.csv",
        mime="text/csv"
    )

    # --- Hadoop Integration (example: save CSV to HDFS) ---
    # This is a placeholder. You must have hdfs3 or pyarrow installed and configured.
    # Uncomment and configure as needed for your Hadoop cluster.
    # import pyarrow as pa
    # import pyarrow.fs as pafs
    # hdfs = pafs.HadoopFileSystem('namenode_host', port=9000, user='your_user')
    # with hdfs.open_output_stream('/user/your_user/all_data_rows.csv') as f:
    #     f.write(csv_all_data)

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
if st.session_state.df is not None and st.session_state.multi_pivots:
    show_all = st.sidebar.checkbox("Show all pivots in one view", value=False)
    # --- Tie Extra2 filter logic ---
    extra2_filter_indices = []
    for idx, pivot in enumerate(st.session_state.multi_pivots):
        for fidx, f in enumerate(pivot.get('filters', [])):
            if f.get('column') == 'Extra2':
                extra2_filter_indices.append((idx, fidx))
    tie_extra2 = False
    if len(extra2_filter_indices) > 1:
        tie_extra2 = st.sidebar.checkbox("Tie Extra2 filter across all pivots", value=False, key="tie_extra2_checkbox")
        if tie_extra2:
            # Find the first non-empty Extra2 value to use as the shared value
            shared_val = None
            for idx, fidx in extra2_filter_indices:
                val = st.session_state.multi_pivots[idx]['filters'][fidx].get('value')
                if val:
                    shared_val = val
                    break
            # Set all Extra2 filter values to the shared value
            if shared_val is not None:
                for idx, fidx in extra2_filter_indices:
                    st.session_state.multi_pivots[idx]['filters'][fidx]['value'] = shared_val
    if show_all:
        for idx, pivot in enumerate(st.session_state.multi_pivots):
            st.markdown(f"---\n### Pivot Table: {pivot['name']}")
            if pivot['pivot_df'] is not None:
                try:
                    styled_pivot_df = pivot['pivot_df'].style.background_gradient(axis=None, cmap="BuPu").set_properties(**{'text-align': 'center'})
                    st.dataframe(styled_pivot_df)
                except Exception:
                    st.dataframe(pivot['pivot_df'].style.set_properties(**{'text-align': 'center'}))
                value_cols = [item['value_col'] for item in pivot['value_agg_list'] if item['value_col']]
                if value_cols:
                    avg_row = {}
                    for col in value_cols:
                        if col in pivot['pivot_df'].columns:
                            vals = pivot['pivot_df'][col].values.flatten()
                        elif isinstance(pivot['pivot_df'].columns, pd.MultiIndex):
                            vals = pivot['pivot_df'].xs(col, axis=1, level=-1, drop_level=False).values.flatten()
                        else:
                            vals = []
                        vals = [v if pd.notna(v) else 0 for v in vals]
                        avg_row[col] = sum(vals) / len(vals) if len(vals) > 0 else 0
                    avg_text = '  '.join([f"<b>Average {col} = {avg_row[col]:.2f}</b>" for col in avg_row])
                    st.markdown(f"<div style='text-align:center; font-size:1.2em; margin: 1em 0;'>{avg_text}</div>", unsafe_allow_html=True)
                st.subheader("Download Pivot Table")
                @st.cache_data
                def convert_pivot_to_csv(df_to_convert):
                    return df_to_convert.to_csv().encode('utf-8')
                csv_data = convert_pivot_to_csv(pivot['pivot_df'])
                pivot_filename = f"pivot_{pivot['name'].replace(' ', '_')}.csv"
                st.download_button(
                    label=f"Download Pivot Table as CSV ({pivot['name']})",
                    data=csv_data,
                    file_name=pivot_filename,
                    mime="text/csv"
                )
                # --- Hadoop Integration for Pivot Table (example) ---
                # Uncomment and configure as needed for your Hadoop cluster.
                # with hdfs.open_output_stream(f'/user/your_user/{pivot_filename}') as f:
                #     f.write(csv_data)
            else:
                st.info(f"No pivot table generated for {pivot['name']} yet.")
    else:
        pivot = st.session_state.multi_pivots[st.session_state.active_pivot]
        source_df = st.session_state.df.copy()
        df_columns = source_df.columns.tolist()

        st.sidebar.header(f"Pivot Table Configuration [{pivot['name']}]")
        pivot['name'] = st.sidebar.text_input("Pivot Name", value=pivot['name'])
        pivot['index_cols'] = st.sidebar.multiselect("Select Row(s) (Index)", options=df_columns, default=pivot['index_cols'])
        pivot['column_cols'] = st.sidebar.multiselect("Select Column(s)", options=df_columns, default=pivot['column_cols'])

        agg_functions = {
            "Sum": "sum",
            "Mean": "mean",
            "Average": "mean",
            "Median": "median",
            "Min": "min",
            "Max": "max",
            "Count": "count",
            "Size": "size",
            "Standard Deviation": "std",
            "Variance": "var",
            "Number of Unique Values": "nunique"
        }

        st.sidebar.subheader("Values & Aggregations")
        if 'value_agg_list' not in pivot or not isinstance(pivot['value_agg_list'], list):
            pivot['value_agg_list'] = []
        def add_value_agg():
            pivot['value_agg_list'].append({"value_col": None, "agg_func": "sum"})
        def remove_value_agg(index):
            if 0 <= index < len(pivot['value_agg_list']):
                pivot['value_agg_list'].pop(index)
        for i, item in enumerate(pivot['value_agg_list']):
            cols_val_agg = st.sidebar.columns([3,3,1])
            with cols_val_agg[0]:
                item["value_col"] = st.selectbox(
                    f"Value Column {i+1}", options=[None] + df_columns,
                    key=f"val_col_{i}_pivot_{st.session_state.active_pivot}",
                    index=([None] + df_columns).index(item["value_col"]) if item["value_col"] in ([None] + df_columns) else 0
                )
            with cols_val_agg[1]:
                selected_agg_name = st.selectbox(
                    f"Aggregation {i+1}", options=list(agg_functions.keys()),
                    key=f"agg_func_{i}_pivot_{st.session_state.active_pivot}",
                    index=list(agg_functions.keys()).index(next((k for k, v in agg_functions.items() if v == item["agg_func"]), "Sum"))
                )
                item["agg_func"] = agg_functions[selected_agg_name]
            with cols_val_agg[2]:
                st.button("➖", key=f"remove_val_agg_{i}_pivot_{st.session_state.active_pivot}", on_click=remove_value_agg, args=(i,))
        st.sidebar.button("Add Value/Aggregation Field", on_click=add_value_agg)

        # --- Source Data Filtering ---
        st.sidebar.subheader("Filter Source Data (Optional)")
        if 'filters' not in pivot or not isinstance(pivot['filters'], list):
            pivot['filters'] = []
        def add_filter():
            pivot['filters'].append({"column": None, "operator": "==", "value": ""})
        def remove_filter(index):
            if 0 <= index < len(pivot['filters']):
                pivot['filters'].pop(index)
        for i, f in enumerate(pivot['filters']):
            filter_cols = st.sidebar.columns([3,2,3,1])
            df_columns = source_df.columns.tolist() if source_df is not None else []
            f['column'] = filter_cols[0].selectbox(
                f"Filter Column {i+1}", [None] + df_columns,
                key=f"filter_col_{i}_pivot_{st.session_state.active_pivot}",
                index=([None] + df_columns).index(f['column']) if f['column'] in ([None] + df_columns) else 0
            )
            try:
                if f["column"] == "Extra2":
                    unique_projects = sorted(source_df["Extra2"].dropna().unique().tolist())
                    f["value"] = filter_cols[2].selectbox(f"Project (Extra2) {i+1}", options=unique_projects, key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}", index=unique_projects.index(f["value"]) if f["value"] in unique_projects else 0)
                else:
                    selected_filter_column = f["column"]
                    available_ops = ["==", "!=", "contains", "does not contain"]
                    is_date_col = False
                    if selected_filter_column and selected_filter_column in source_df.columns:
                        try:
                            if pd.api.types.is_datetime64_any_dtype(source_df[selected_filter_column]):
                                is_date_col = True
                            else:
                                sample = source_df[selected_filter_column].dropna().iloc[:5]
                                if not sample.empty and pd.to_datetime(sample, errors='coerce').notna().all():
                                    is_date_col = True
                        except (TypeError, ValueError, AttributeError):
                            is_date_col = False
                        if is_date_col:
                            available_ops = ["is exactly", "is not", "is after", "is on or after",
                                             "is before", "is on or before", "is between (inclusive)",
                                             "is current month", "is previous month", "is next month",
                                             "is current year", "is previous year", "is next year"]
                        elif pd.api.types.is_numeric_dtype(source_df[selected_filter_column]):
                            available_ops = ["==", "!=", ">", "<", ">=", "<="]
                    f["operator"] = filter_cols[1].selectbox(f"Operator {i+1}", available_ops, key=f"filter_op_{i}_pivot_{st.session_state.active_pivot}", index=available_ops.index(f["operator"]) if f["operator"] in available_ops else 0)
                    if is_date_col and f["operator"] == "is between (inclusive)":
                        val_start_key = f"filter_val_start_{i}_pivot_{st.session_state.active_pivot}"
                        val_end_key = f"filter_val_end_{i}_pivot_{st.session_state.active_pivot}"
                        if not isinstance(f["value"], list) or len(f["value"]) != 2:
                            f["value"] = [source_df[selected_filter_column].min(), source_df[selected_filter_column].max()]
                        f["value"][0] = filter_cols[2].date_input("Start date", value=pd.to_datetime(f["value"][0]), key=val_start_key)
                        f["value"][1] = filter_cols[2].date_input("End date", value=pd.to_datetime(f["value"][1]), key=val_end_key)
                    elif is_date_col and f["operator"] in ["is exactly", "is not", "is after", "is on or after", "is before", "is on or before"]:
                        default_date_val = pd.to_datetime(f["value"], errors='coerce')
                        if pd.isna(default_date_val):
                            default_date_val = datetime.now().date()
                        f["value"] = filter_cols[2].date_input(f"Date {i+1}", value=default_date_val, key=f"filter_val_date_{i}_pivot_{st.session_state.active_pivot}")
                    elif is_date_col and f["operator"] in ["is current month", "is previous month", "is next month", "is current year", "is previous year", "is next year"]:
                        filter_cols[2].markdown(f"*{f['operator']}* (no value needed)", unsafe_allow_html=True)
                        f["value"] = None
                    elif selected_filter_column and pd.api.types.is_numeric_dtype(source_df[selected_filter_column]):
                        f["value"] = filter_cols[2].number_input(f"Value {i+1}", value=pd.to_numeric(f["value"], errors='coerce'), key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}")
                    elif selected_filter_column and (pd.api.types.is_categorical_dtype(source_df[selected_filter_column]) or (source_df[selected_filter_column].nunique() < 20 and source_df[selected_filter_column].nunique() > 1)):
                        unique_vals = [""] + source_df[selected_filter_column].unique().tolist()
                        f["value"] = filter_cols[2].selectbox(f"Value {i+1}", options=unique_vals, key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}", index=unique_vals.index(f["value"]) if f["value"] in unique_vals else 0)
                    else:
                        f["value"] = filter_cols[2].text_input(f"Value {i+1}", value=str(f["value"]), key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}")
                filter_cols[3].button("➖", key=f"remove_filter_{i}_pivot_{st.session_state.active_pivot}", on_click=remove_filter, args=(i,))
            except Exception:
                continue
        st.sidebar.button("Add Filter", on_click=add_filter)

        # --- Apply Filters ---
        filtered_df = source_df.copy()
        for f_config in pivot['filters']:
            if f_config["column"] and (f_config["value"] is not None or isinstance(f_config["value"], list)):
                col = f_config["column"]
                op = f_config["operator"]
                val_config = f_config["value"]
                try:
                    is_date_op = op in ["is exactly", "is not", "is after", "is on or after",
                                        "is before", "is on or before", "is between (inclusive)",
                                        "is current month", "is previous month", "is next month",
                                        "is current year", "is previous year", "is next year"]
                    col_data = filtered_df[col]
                    if is_date_op:
                        col_data_dt = pd.to_datetime(filtered_df[col], errors='coerce')
                        valid_date_mask = col_data_dt.notna()
                        if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                            valid_date_mask = valid_date_mask | filtered_df[col].isna()
                        filtered_df = filtered_df[valid_date_mask]
                        col_data_dt = col_data_dt[valid_date_mask]
                    if op == "is between (inclusive)" and is_date_op:
                        if isinstance(val_config, list) and len(val_config) == 2:
                            start_date, end_date = pd.to_datetime(val_config[0]), pd.to_datetime(val_config[1])
                            if not pd.isna(start_date) and not pd.isna(end_date):
                                filtered_df = filtered_df[col_data_dt.between(start_date, end_date)]
                    elif is_date_op:
                        today = pd.Timestamp.now().normalize()
                        if op == "is current month":
                            filtered_df = filtered_df[(col_data_dt.dt.year == today.year) & (col_data_dt.dt.month == today.month)]
                        elif op == "is previous month":
                            current_month_start = today.replace(day=1)
                            prev_month_end = current_month_start - timedelta(days=1)
                            prev_month_start = prev_month_end.replace(day=1)
                            filtered_df = filtered_df[col_data_dt.between(prev_month_start, prev_month_end, inclusive="both")]
                        elif op == "is next month":
                            current_month_end = today + pd.offsets.MonthEnd(0)
                            next_month_start = current_month_end + timedelta(days=1)
                            next_month_end = next_month_start + pd.offsets.MonthEnd(0)
                            filtered_df = filtered_df[col_data_dt.between(next_month_start, next_month_end, inclusive="both")]
                        elif op == "is current year":
                            filtered_df = filtered_df[col_data_dt.dt.year == today.year]
                        elif op == "is previous year":
                            filtered_df = filtered_df[col_data_dt.dt.year == today.year - 1]
                        elif op == "is next year":
                            filtered_df = filtered_df[col_data_dt.dt.year == today.year + 1]
                        else:
                            val_dt = pd.to_datetime(val_config, errors='coerce')
                            if not pd.isna(val_dt):
                                if op == "is exactly": filtered_df = filtered_df[col_data_dt == val_dt]
                                elif op == "is not": filtered_df = filtered_df[col_data_dt != val_dt]
                                elif op == "is after": filtered_df = filtered_df[col_data_dt > val_dt]
                                elif op == "is on or after": filtered_df = filtered_df[col_data_dt >= val_dt]
                                elif op == "is before": filtered_df = filtered_df[col_data_dt < val_dt]
                                elif op == "is on or before": filtered_df = filtered_df[col_data_dt <= val_dt]
                    else:
                        val_str = str(val_config)
                        val = val_config
                        if pd.api.types.is_numeric_dtype(col_data) and op not in ["contains", "does not contain"]:
                            val = pd.to_numeric(val_str, errors='coerce')
                            if pd.isna(val): continue
                        elif op in ["contains", "does not contain"]:
                            col_data_str = col_data.astype(str)
                            if op == "contains": filtered_df = filtered_df[col_data_str.str.contains(val_str, case=False, na=False)]
                            elif op == "does not contain": filtered_df = filtered_df[~col_data_str.str.contains(val_str, case=False, na=False)]
                            continue
                        if op == "==": filtered_df = filtered_df[col_data == val]
                        elif op == "!=": filtered_df = filtered_df[col_data != val]
                        elif op == ">": filtered_df = filtered_df[col_data > val]
                        elif op == "<": filtered_df = filtered_df[col_data < val]
                        elif op == ">=": filtered_df = filtered_df[col_data >= val]
                        elif op == "<=": filtered_df = filtered_df[col_data <= val]
                except Exception as e:
                    st.sidebar.warning(f"Could not apply filter on '{col}' with value '{val_config}': {e}")
        # --- Fill Value & Margins ---
        pivot['fill_value_enabled'] = st.sidebar.checkbox("Fill missing values (NaN)?", value=pivot['fill_value_enabled'])
        if pivot['fill_value_enabled']:
            custom_fill_value_str = st.sidebar.text_input("Enter value to fill NaN with (e.g., 0)", str(pivot['custom_fill_value']) if pivot['custom_fill_value'] is not None else "0")
            try:
                custom_fill_value = float(custom_fill_value_str)
                if custom_fill_value.is_integer():
                    custom_fill_value = int(custom_fill_value)
                pivot['custom_fill_value'] = custom_fill_value
            except ValueError:
                pivot['custom_fill_value'] = custom_fill_value_str
        else:
            pivot['custom_fill_value'] = None
        pivot['margins_enabled'] = st.sidebar.checkbox("Show Totals (Margins)?", value=pivot['margins_enabled'])
        if pivot['margins_enabled']:
            pivot['margins_name'] = st.sidebar.text_input("Name for Totals/Margins", value=pivot['margins_name'])
        # --- Generate Pivot Table ---
        # --- Error and Code Logging ---
        if 'error_log' not in pivot:
            pivot['error_log'] = ''
        def log_error(msg):
            if msg:
                pivot['error_log'] += str(msg) + '\n'
        # Make log_error available in this scope
        pivot['log_error'] = log_error
        if st.sidebar.button("Create Pivot Table", key=f"create_pivot_{st.session_state.active_pivot}"):
            value_cols_for_pivot = [item["value_col"] for item in pivot['value_agg_list'] if item["value_col"]]
            aggfunc_dict = {item["value_col"]: item["agg_func"] for item in pivot['value_agg_list'] if item["value_col"]}
            if not pivot['index_cols'] and not pivot['column_cols']:
                pivot['log_error']("Please select at least one field for Rows or Columns.")
                pivot['pivot_df'] = None
            elif not value_cols_for_pivot and not any(item["agg_func"] in ['size'] for item in pivot['value_agg_list']):
                pivot['log_error']("Please add and select at least one Value Column and Aggregation.")
                pivot['pivot_df'] = None
            else:
                try:
                    pivot_params = {
                        "index": pivot['index_cols'] if pivot['index_cols'] else None,
                        "columns": pivot['column_cols'] if pivot['column_cols'] else None,
                        "values": value_cols_for_pivot if value_cols_for_pivot else None,
                        "aggfunc": aggfunc_dict if aggfunc_dict else 'size'
                    }
                    if pivot['fill_value_enabled']:
                        pivot_params["fill_value"] = pivot['custom_fill_value']
                    if pivot['margins_enabled']:
                        pivot_params["margins"] = True
                        pivot_params["margins_name"] = pivot['margins_name']
                    pivot_params = {k: v for k, v in pivot_params.items() if v is not None or k in ["fill_value", "margins", "margins_name"]}
                    pivot['pivot_df'] = pd.pivot_table(filtered_df, **pivot_params)
                except Exception as e:
                    pivot['pivot_df'] = None
                    pivot['log_error'](f"Error creating pivot table: {e}")
        # --- Display Pivot Table ---
        if pivot['pivot_df'] is not None:
            st.subheader(f"Generated Pivot Table [{pivot['name']}]")
            try:
                styled_pivot_df = pivot['pivot_df'].style.background_gradient(axis=None, cmap="BuPu").set_properties(**{'text-align': 'center'})
                st.dataframe(styled_pivot_df)
            except Exception as e:
                st.warning(f"Could not apply styling to the pivot table: {e}. Displaying raw table.")
                st.dataframe(pivot['pivot_df'].style.set_properties(**{'text-align': 'center'}))
            # --- Show Average Row ---
            value_cols = [item['value_col'] for item in pivot['value_agg_list'] if item['value_col']]
            if value_cols:
                avg_row = {}
                for col in value_cols:
                    if col in pivot['pivot_df'].columns:
                        vals = pivot['pivot_df'][col].values.flatten()
                    elif isinstance(pivot['pivot_df'].columns, pd.MultiIndex):
                        vals = pivot['pivot_df'].xs(col, axis=1, level=-1, drop_level=False).values.flatten()
                    else:
                        vals = []
                    vals = [v if pd.notna(v) else 0 for v in vals]
                    avg_row[col] = sum(vals) / len(vals) if len(vals) > 0 else 0
                avg_text = '  '.join([f"<b>Average {col} = {avg_row[col]:.2f}</b>" for col in avg_row])
                st.markdown(f"<div style='text-align:center; font-size:1.2em; margin: 1em 0;'>{avg_text}</div>", unsafe_allow_html=True)
            st.subheader("Download Pivot Table")
            @st.cache_data
            def convert_pivot_to_csv(df_to_convert):
                return df_to_convert.to_csv().encode('utf-8')
            csv_data = convert_pivot_to_csv(pivot['pivot_df'])
            pivot_filename = f"pivot_{pivot['name'].replace(' ', '_')}.csv"
            st.download_button(
                label="Download Pivot Table as CSV",
                data=csv_data,
                file_name=pivot_filename,
                mime="text/csv"
            )
            # --- Hadoop Integration for Pivot Table (example) ---
            # Uncomment and configure as needed for your Hadoop cluster.
            # with hdfs.open_output_stream(f'/user/your_user/{pivot_filename}') as f:
            #     f.write(csv_data)
        # --- Download Buttons for Code and Error Log ---
        if pivot['generated_code']:
            st.download_button(
                label="Download Generated Python Code",
                data=pivot['generated_code'],
                file_name=f"pivot_code_{pivot['name'].replace(' ', '_')}.py",
                mime="text/x-python"
            )
        if pivot['error_log']:
            st.download_button(
                label="Download Error Log",
                data=pivot['error_log'],
                file_name=f"pivot_error_log_{pivot['name'].replace(' ', '_')}.txt",
                mime="text/plain"
            )
# --- Initial Message ---
elif st.session_state.df is None:
    st.info(
        "Welcome to the Interactive Multi-Pivot Table Creator! 🎉\n\n"
        "1. **Upload your CSV file** using the sidebar.\n"
        "2. **Configure your pivots**: Add new pivots, select rows/columns, and define aggregations.\n"
        "3. **View and download** your pivot tables and the generated Python code for your pivots.\n\n"
        "This app allows you to create multiple pivot tables from your data, with flexible options for rows, columns, values, and filters. You can also tie the Extra2 filter across pivots for consistent filtering.\n\n"
        "Get started by uploading a CSV file with your data!"
    )