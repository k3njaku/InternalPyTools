import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import datetime as dt

"""An improved version of `pivot_tool.py` and `pivottools_v2.py`.

Features:
- Multiple pivot configurations with ability to save/load views.
- Display and download of the original dataset.
- Advanced filtering options including date operations.
- Optional generation of Python code representing the pivot logic.
- Commented hooks for Hadoop/HDFS integration.
"""

st.set_page_config(layout="wide")
st.title("Interactive Multi-Pivot Table Creator (Codex)")

# -------------------------------------------------------------
# Session State initialisation
# -------------------------------------------------------------
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'multi_pivots' not in st.session_state:
    st.session_state.multi_pivots = []
if 'active_pivot' not in st.session_state:
    st.session_state.active_pivot = 0

# -------------------------------------------------------------
# File upload
# -------------------------------------------------------------
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    if st.session_state.uploaded_file_name != uploaded_file.name:
        try:
            df_tmp = pd.read_csv(uploaded_file)
            for col in df_tmp.columns:
                if df_tmp[col].dtype == object:
                    df_tmp[col] = df_tmp[col].replace("0000-00-00", pd.NA)
                    try:
                        df_tmp[col] = pd.to_datetime(df_tmp[col], errors="ignore")
                    except Exception:
                        pass
            st.session_state.df = df_tmp
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

# -------------------------------------------------------------
# Helpers for saving/loading views
# -------------------------------------------------------------
SAVED_VIEWS_FILE = "saved_pivot_views.json"

def serialize_dates(obj):
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_dates(v) for v in obj]
    if isinstance(obj, (dt.date, dt.datetime)):
        return obj.isoformat()
    return obj

def default_pivot_config(df):
    return {
        "name": f"Pivot {len(st.session_state.multi_pivots)+1}",
        "index_cols": [],
        "column_cols": [],
        "value_agg_list": [],
        "filters": [],
        "fill_value_enabled": False,
        "custom_fill_value": None,
        "margins_enabled": False,
        "margins_name": "All_Totals",
        "pivot_df": None,
        "filtered_df": None,
        "generated_code": None,
        "error_log": "",
    }

def save_views():
    with open(SAVED_VIEWS_FILE, "w") as f:
        json.dump([
            serialize_dates({k: v for k, v in p.items() if k not in ["pivot_df", "filtered_df"]})
            for p in st.session_state.multi_pivots
        ], f)

def load_views():
    try:
        with open(SAVED_VIEWS_FILE, "r") as f:
            loaded = json.load(f)
            for p in loaded:
                p["pivot_df"] = None
                p["filtered_df"] = None
            st.session_state.multi_pivots = loaded
            st.session_state.active_pivot = 0
    except Exception:
        pass

if st.sidebar.button("Save All Views"):
    save_views()
if st.sidebar.button("Load Saved Views"):
    load_views()

# -------------------------------------------------------------
# Show raw data section
# -------------------------------------------------------------
if st.session_state.df is not None:
    st.subheader("All Data Rows")
    st.dataframe(st.session_state.df, use_container_width=True)
    csv_all = st.session_state.df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download All Data Rows as CSV",
        csv_all,
        "all_data_rows.csv",
        "text/csv",
    )
    # Hadoop integration (optional)
    # import pyarrow.fs as pafs
    # hdfs = pafs.HadoopFileSystem('namenode_host', port=9000, user='your_user')
    # with hdfs.open_output_stream('/user/your_user/all_data_rows.csv') as f:
    #     f.write(csv_all)

# -------------------------------------------------------------
# Pivot management controls
# -------------------------------------------------------------
if st.session_state.df is not None:
    st.sidebar.markdown("## Manage Pivots")
    if st.sidebar.button("Add New Pivot"):
        st.session_state.multi_pivots.append(default_pivot_config(st.session_state.df))
        st.session_state.active_pivot = len(st.session_state.multi_pivots) - 1
    if st.session_state.multi_pivots:
        names = [p["name"] for p in st.session_state.multi_pivots]
        st.session_state.active_pivot = st.sidebar.selectbox(
            "Select Pivot",
            options=list(range(len(names))),
            format_func=lambda i: names[i],
            index=min(st.session_state.active_pivot, len(names)-1),
        )
        if st.sidebar.button("Remove Selected Pivot") and len(st.session_state.multi_pivots) > 0:
            st.session_state.multi_pivots.pop(st.session_state.active_pivot)
            st.session_state.active_pivot = max(0, st.session_state.active_pivot - 1)

# -------------------------------------------------------------
# Main pivot UI
# -------------------------------------------------------------
if st.session_state.df is not None and st.session_state.multi_pivots:
    show_all = st.sidebar.checkbox("Show all pivots in one view", value=False)

    # tie Extra2 filter across pivots
    extra2_filter_indices = []
    for idx, pivot in enumerate(st.session_state.multi_pivots):
        for fidx, f in enumerate(pivot.get("filters", [])):
            if f.get("column") == "Extra2":
                extra2_filter_indices.append((idx, fidx))
    if len(extra2_filter_indices) > 1:
        tie_extra2 = st.sidebar.checkbox("Tie Extra2 filter across all pivots", value=False)
        if tie_extra2:
            shared = None
            for idx, fidx in extra2_filter_indices:
                val = st.session_state.multi_pivots[idx]["filters"][fidx].get("value")
                if val:
                    shared = val
                    break
            if shared is not None:
                for idx, fidx in extra2_filter_indices:
                    st.session_state.multi_pivots[idx]["filters"][fidx]["value"] = shared

    if show_all:
        for pivot in st.session_state.multi_pivots:
            st.markdown(f"---\n### Pivot Table: {pivot['name']}")
            if pivot["pivot_df"] is not None:
                try:
                    st.dataframe(pivot["pivot_df"].style.background_gradient(axis=None, cmap="BuPu").set_properties(**{"text-align": "center"}))
                except Exception:
                    st.dataframe(pivot["pivot_df"].style.set_properties(**{"text-align": "center"}))
                _vals = [it["value_col"] for it in pivot["value_agg_list"] if it["value_col"]]
                if _vals:
                    avg_row = {}
                    for col in _vals:
                        if col in pivot["pivot_df"].columns:
                            vals = pivot["pivot_df"][col].values.flatten()
                        elif isinstance(pivot["pivot_df"].columns, pd.MultiIndex):
                            vals = pivot["pivot_df"].xs(col, axis=1, level=-1, drop_level=False).values.flatten()
                        else:
                            vals = []
                        vals = [v if pd.notna(v) else 0 for v in vals]
                        avg_row[col] = sum(vals) / len(vals) if vals else 0
                    txt = "  ".join([f"<b>Average {c} = {avg_row[c]:.2f}</b>" for c in avg_row])
                    st.markdown(f"<div style='text-align:center; font-size:1.2em; margin: 1em 0;'>{txt}</div>", unsafe_allow_html=True)
                csv_data = pivot["pivot_df"].to_csv().encode("utf-8")
                st.download_button(
                    label=f"Download Pivot Table as CSV ({pivot['name']})",
                    data=csv_data,
                    file_name=f"pivot_{pivot['name'].replace(' ', '_')}.csv",
                    mime="text/csv",
                )
                if pivot.get("filtered_df") is not None:
                    st.subheader(f"Filtered Data Rows [{pivot['name']}]")
                    st.dataframe(pivot["filtered_df"], use_container_width=True)
                    filtered_csv = pivot["filtered_df"].to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label=f"Download Filtered Data as CSV ({pivot['name']})",
                        data=filtered_csv,
                        file_name=f"filtered_data_{pivot['name'].replace(' ', '_')}.csv",
                        mime="text/csv",
                    )
                if pivot.get("generated_code"):
                    st.download_button(
                        label=f"Download Python Code ({pivot['name']})",
                        data=pivot["generated_code"],
                        file_name=f"pivot_code_{pivot['name'].replace(' ', '_')}.py",
                        mime="text/x-python",
                    )
                if pivot.get("error_log"):
                    st.download_button(
                        label=f"Download Error Log ({pivot['name']})",
                        data=pivot["error_log"],
                        file_name=f"pivot_error_log_{pivot['name'].replace(' ', '_')}.txt",
                        mime="text/plain",
                    )
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
            "Number of Unique Values": "nunique",
        }

        st.sidebar.subheader("Values & Aggregations")
        if 'value_agg_list' not in pivot or not isinstance(pivot['value_agg_list'], list):
            pivot['value_agg_list'] = []

        def add_value_agg():
            pivot['value_agg_list'].append({"value_col": None, "agg_func": "sum"})

        def remove_value_agg(idx):
            if 0 <= idx < len(pivot['value_agg_list']):
                pivot['value_agg_list'].pop(idx)

        for i, item in enumerate(pivot['value_agg_list']):
            cols = st.sidebar.columns([3, 3, 1])
            with cols[0]:
                item['value_col'] = st.selectbox(
                    f"Value Column {i+1}", [None] + df_columns,
                    key=f"val_col_{i}_pivot_{st.session_state.active_pivot}",
                    index=([None] + df_columns).index(item['value_col']) if item['value_col'] in ([None] + df_columns) else 0,
                )
            with cols[1]:
                sel_name = st.selectbox(
                    f"Aggregation {i+1}", list(agg_functions.keys()),
                    key=f"agg_func_{i}_pivot_{st.session_state.active_pivot}",
                    index=list(agg_functions.keys()).index(next((k for k, v in agg_functions.items() if v == item['agg_func']), 'Sum')),
                )
                item['agg_func'] = agg_functions[sel_name]
            with cols[2]:
                st.button("➖", key=f"remove_val_agg_{i}_pivot_{st.session_state.active_pivot}", on_click=remove_value_agg, args=(i,))
        st.sidebar.button("Add Value/Aggregation Field", on_click=add_value_agg)

        # -----------------------------------------------------
        # Filters
        # -----------------------------------------------------
        st.sidebar.subheader("Filter Source Data (Optional)")
        if 'filters' not in pivot or not isinstance(pivot['filters'], list):
            pivot['filters'] = []

        def add_filter():
            pivot['filters'].append({"column": None, "operator": "==", "value": ""})

        def remove_filter(idx):
            if 0 <= idx < len(pivot['filters']):
                pivot['filters'].pop(idx)

        for i, f in enumerate(pivot['filters']):
            f_cols = st.sidebar.columns([3, 2, 3, 1])
            df_cols = source_df.columns.tolist() if source_df is not None else []
            f['column'] = f_cols[0].selectbox(
                f"Filter Column {i+1}", [None] + df_cols,
                key=f"filter_col_{i}_pivot_{st.session_state.active_pivot}",
                index=([None] + df_cols).index(f['column']) if f['column'] in ([None] + df_cols) else 0,
            )
            try:
                if f['column'] == 'Extra2':
                    unique_projects = sorted(source_df['Extra2'].dropna().unique().tolist())
                    f['value'] = f_cols[2].selectbox(
                        f"Project (Extra2) {i+1}", unique_projects,
                        key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}",
                        index=unique_projects.index(f['value']) if f['value'] in unique_projects else 0,
                    )
                else:
                    selected = f['column']
                    ops = ['==', '!=', 'contains', 'does not contain']
                    is_date = False
                    if selected and selected in source_df.columns:
                        try:
                            if pd.api.types.is_datetime64_any_dtype(source_df[selected]):
                                is_date = True
                            else:
                                sample = source_df[selected].dropna().iloc[:5]
                                if not sample.empty and pd.to_datetime(sample, errors='coerce').notna().all():
                                    is_date = True
                        except (TypeError, ValueError, AttributeError):
                            is_date = False
                        if is_date:
                            ops = [
                                'is exactly', 'is not', 'is after', 'is on or after',
                                'is before', 'is on or before', 'is between (inclusive)',
                                'is current month', 'is previous month', 'is next month',
                                'is current year', 'is previous year', 'is next year',
                            ]
                        elif pd.api.types.is_numeric_dtype(source_df[selected]):
                            ops = ['==', '!=', '>', '<', '>=', '<=']
                    f['operator'] = f_cols[1].selectbox(
                        f"Operator {i+1}", ops,
                        key=f"filter_op_{i}_pivot_{st.session_state.active_pivot}",
                        index=ops.index(f['operator']) if f['operator'] in ops else 0,
                    )
                    if is_date and f['operator'] == 'is between (inclusive)':
                        start_key = f"filter_val_start_{i}_pivot_{st.session_state.active_pivot}"
                        end_key = f"filter_val_end_{i}_pivot_{st.session_state.active_pivot}"
                        if not isinstance(f['value'], list) or len(f['value']) != 2:
                            f['value'] = [source_df[selected].min(), source_df[selected].max()]
                        f['value'][0] = f_cols[2].date_input('Start date', value=pd.to_datetime(f['value'][0]), key=start_key)
                        f['value'][1] = f_cols[2].date_input('End date', value=pd.to_datetime(f['value'][1]), key=end_key)
                    elif is_date and f['operator'] in ['is exactly', 'is not', 'is after', 'is on or after', 'is before', 'is on or before']:
                        default_val = pd.to_datetime(f['value'], errors='coerce')
                        if pd.isna(default_val):
                            default_val = datetime.now().date()
                        f['value'] = f_cols[2].date_input(f'Date {i+1}', value=default_val, key=f"filter_val_date_{i}_pivot_{st.session_state.active_pivot}")
                    elif is_date and f['operator'] in ['is current month', 'is previous month', 'is next month', 'is current year', 'is previous year', 'is next year']:
                        f_cols[2].markdown(f"*{f['operator']}* (no value needed)", unsafe_allow_html=True)
                        f['value'] = None
                    elif selected and pd.api.types.is_numeric_dtype(source_df[selected]):
                        f['value'] = f_cols[2].number_input(
                            f"Value {i+1}",
                            value=pd.to_numeric(f['value'], errors='coerce'),
                            key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}",
                        )
                    elif selected and (pd.api.types.is_categorical_dtype(source_df[selected]) or (0 < source_df[selected].nunique() < 20)):
                        unique_vals = [''] + source_df[selected].unique().tolist()
                        f['value'] = f_cols[2].selectbox(
                            f"Value {i+1}", unique_vals,
                            key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}",
                            index=unique_vals.index(f['value']) if f['value'] in unique_vals else 0,
                        )
                    else:
                        f['value'] = f_cols[2].text_input(
                            f"Value {i+1}",
                            value=str(f['value']),
                            key=f"filter_val_{i}_pivot_{st.session_state.active_pivot}",
                        )
                f_cols[3].button("➖", key=f"remove_filter_{i}_pivot_{st.session_state.active_pivot}", on_click=remove_filter, args=(i,))
            except Exception:
                continue
        st.sidebar.button("Add Filter", on_click=add_filter)

        # apply filters to dataframe
        filtered_df = source_df.copy()
        for f_cfg in pivot['filters']:
            if f_cfg['column'] and (f_cfg['value'] is not None or isinstance(f_cfg['value'], list)):
                col = f_cfg['column']
                op = f_cfg['operator']
                val_cfg = f_cfg['value']
                try:
                    date_ops = [
                        'is exactly', 'is not', 'is after', 'is on or after',
                        'is before', 'is on or before', 'is between (inclusive)',
                        'is current month', 'is previous month', 'is next month',
                        'is current year', 'is previous year', 'is next year',
                    ]
                    col_data = filtered_df[col]
                    if op in date_ops:
                        col_dt = pd.to_datetime(filtered_df[col], errors='coerce')
                        valid_mask = col_dt.notna()
                        if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                            valid_mask = valid_mask | filtered_df[col].isna()
                        filtered_df = filtered_df[valid_mask]
                        col_dt = col_dt[valid_mask]
                    if op == 'is between (inclusive)' and op in date_ops:
                        if isinstance(val_cfg, list) and len(val_cfg) == 2:
                            start, end = pd.to_datetime(val_cfg[0]), pd.to_datetime(val_cfg[1])
                            if not pd.isna(start) and not pd.isna(end):
                                filtered_df = filtered_df[col_dt.between(start, end)]
                    elif op in date_ops:
                        today = pd.Timestamp.now().normalize()
                        if op == 'is current month':
                            filtered_df = filtered_df[(col_dt.dt.year == today.year) & (col_dt.dt.month == today.month)]
                        elif op == 'is previous month':
                            start_month = today.replace(day=1)
                            prev_end = start_month - timedelta(days=1)
                            prev_start = prev_end.replace(day=1)
                            filtered_df = filtered_df[col_dt.between(prev_start, prev_end, inclusive='both')]
                        elif op == 'is next month':
                            month_end = today + pd.offsets.MonthEnd(0)
                            next_start = month_end + timedelta(days=1)
                            next_end = next_start + pd.offsets.MonthEnd(0)
                            filtered_df = filtered_df[col_dt.between(next_start, next_end, inclusive='both')]
                        elif op == 'is current year':
                            filtered_df = filtered_df[col_dt.dt.year == today.year]
                        elif op == 'is previous year':
                            filtered_df = filtered_df[col_dt.dt.year == today.year - 1]
                        elif op == 'is next year':
                            filtered_df = filtered_df[col_dt.dt.year == today.year + 1]
                        else:
                            val_dt = pd.to_datetime(val_cfg, errors='coerce')
                            if not pd.isna(val_dt):
                                if op == 'is exactly':
                                    filtered_df = filtered_df[col_dt == val_dt]
                                elif op == 'is not':
                                    filtered_df = filtered_df[col_dt != val_dt]
                                elif op == 'is after':
                                    filtered_df = filtered_df[col_dt > val_dt]
                                elif op == 'is on or after':
                                    filtered_df = filtered_df[col_dt >= val_dt]
                                elif op == 'is before':
                                    filtered_df = filtered_df[col_dt < val_dt]
                                elif op == 'is on or before':
                                    filtered_df = filtered_df[col_dt <= val_dt]
                    else:
                        val_str = str(val_cfg)
                        val = val_cfg
                        if pd.api.types.is_numeric_dtype(col_data) and op not in ['contains', 'does not contain']:
                            val = pd.to_numeric(val_str, errors='coerce')
                            if pd.isna(val):
                                continue
                        elif op in ['contains', 'does not contain']:
                            col_str = col_data.astype(str)
                            if op == 'contains':
                                filtered_df = filtered_df[col_str.str.contains(val_str, case=False, na=False)]
                            else:
                                filtered_df = filtered_df[~col_str.str.contains(val_str, case=False, na=False)]
                            continue
                        if op == '==':
                            filtered_df = filtered_df[col_data == val]
                        elif op == '!=':
                            filtered_df = filtered_df[col_data != val]
                        elif op == '>':
                            filtered_df = filtered_df[col_data > val]
                        elif op == '<':
                            filtered_df = filtered_df[col_data < val]
                        elif op == '>=':
                            filtered_df = filtered_df[col_data >= val]
                        elif op == '<=':
                            filtered_df = filtered_df[col_data <= val]
                except Exception as e:
                    st.sidebar.warning(f"Could not apply filter on '{col}' with value '{val_cfg}': {e}")

        pivot['filtered_df'] = filtered_df

        # fill value and margins
        pivot['fill_value_enabled'] = st.sidebar.checkbox("Fill missing values (NaN)?", value=pivot['fill_value_enabled'])
        if pivot['fill_value_enabled']:
            fill_str = st.sidebar.text_input("Enter value to fill NaN with (e.g., 0)",
                                            str(pivot['custom_fill_value']) if pivot['custom_fill_value'] is not None else '0')
            try:
                fill_val = float(fill_str)
                if fill_val.is_integer():
                    fill_val = int(fill_val)
                pivot['custom_fill_value'] = fill_val
            except ValueError:
                pivot['custom_fill_value'] = fill_str
        else:
            pivot['custom_fill_value'] = None

        pivot['margins_enabled'] = st.sidebar.checkbox("Show Totals (Margins)?", value=pivot['margins_enabled'])
        if pivot['margins_enabled']:
            pivot['margins_name'] = st.sidebar.text_input("Name for Totals/Margins", value=pivot['margins_name'])

        # -----------------------------------------------------
        # Create Pivot Table
        # -----------------------------------------------------
        if 'error_log' not in pivot:
            pivot['error_log'] = ''

        def log_error(msg):
            if msg:
                pivot['error_log'] += str(msg) + '\n'
        pivot['log_error'] = log_error

        if st.sidebar.button("Create Pivot Table", key=f"create_pivot_{st.session_state.active_pivot}"):
            vals_for_pivot = [it['value_col'] for it in pivot['value_agg_list'] if it['value_col']]
            aggfunc_dict = {it['value_col']: it['agg_func'] for it in pivot['value_agg_list'] if it['value_col']}
            if not pivot['index_cols'] and not pivot['column_cols']:
                pivot['log_error']("Please select at least one field for Rows or Columns.")
                pivot['pivot_df'] = None
            elif not vals_for_pivot and not any(it['agg_func'] in ['size'] for it in pivot['value_agg_list']):
                pivot['log_error']("Please add and select at least one Value Column and Aggregation.")
                pivot['pivot_df'] = None
            else:
                try:
                    params = {
                        'index': pivot['index_cols'] if pivot['index_cols'] else None,
                        'columns': pivot['column_cols'] if pivot['column_cols'] else None,
                        'values': vals_for_pivot if vals_for_pivot else None,
                        'aggfunc': aggfunc_dict if aggfunc_dict else 'size',
                    }
                    if pivot['fill_value_enabled']:
                        params['fill_value'] = pivot['custom_fill_value']
                    if pivot['margins_enabled']:
                        params['margins'] = True
                        params['margins_name'] = pivot['margins_name']
                    params = {k: v for k, v in params.items() if v is not None or k in ['fill_value', 'margins', 'margins_name']}
                    pivot['pivot_df'] = pd.pivot_table(filtered_df, **params)
                except Exception as e:
                    pivot['pivot_df'] = None
                    pivot['log_error'](f"Error creating pivot table: {e}")

        # -----------------------------------------------------
        # Generate Python Code from current config
        # -----------------------------------------------------
        def generate_python_code():
            lines = [
                'import pandas as pd',
                'from datetime import datetime, timedelta\n',
                '# Load your DataFrame here',
                "df_original = pd.DataFrame()  # replace with actual load",\
                "\ndf_filtered = df_original.copy()\n",
                '# Apply Filters',
            ]
            if not pivot['filters']:
                lines.append('# No filters applied.')
            active_filters = [f for f in pivot['filters'] if f['column'] and (f['value'] is not None or isinstance(f['value'], list) or f['operator'] in ['is current month', 'is previous month', 'is next month', 'is current year', 'is previous year', 'is next year'])]
            for i, f_cfg in enumerate(active_filters):
                col = f_cfg['column']
                op = f_cfg['operator']
                val_cfg = f_cfg['value']
                is_date = op in [
                    'is exactly', 'is not', 'is after', 'is on or after',
                    'is before', 'is on or before', 'is between (inclusive)',
                    'is current month', 'is previous month', 'is next month',
                    'is current year', 'is previous year', 'is next year',
                ]
                if is_date:
                    lines.append(f"df_filtered['{col}'] = pd.to_datetime(df_filtered['{col}'], errors='coerce')")
                    lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].notna()]")
                    if op == 'is between (inclusive)':
                        start = pd.to_datetime(val_cfg[0]).strftime('%Y-%m-%d')
                        end = pd.to_datetime(val_cfg[1]).strftime('%Y-%m-%d')
                        lines.append(f"start_{i} = pd.to_datetime('{start}')")
                        lines.append(f"end_{i} = pd.to_datetime('{end}')")
                        lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].between(start_{i}, end_{i}, inclusive='both')]")
                    elif op in ['is current month', 'is previous month', 'is next month', 'is current year', 'is previous year', 'is next year']:
                        lines.append(f"today_{i} = pd.Timestamp.now().normalize()")
                        if op == 'is current month':
                            lines.append(f"df_filtered = df_filtered[(df_filtered['{col}'].dt.year == today_{i}.year) & (df_filtered['{col}'].dt.month == today_{i}.month)]")
                        elif op == 'is previous month':
                            lines.append(f"current_month_start_{i} = today_{i}.replace(day=1)")
                            lines.append(f"prev_month_end_{i} = current_month_start_{i} - timedelta(days=1)")
                            lines.append(f"prev_month_start_{i} = prev_month_end_{i}.replace(day=1)")
                            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].between(prev_month_start_{i}, prev_month_end_{i}, inclusive='both')]")
                        elif op == 'is next month':
                            lines.append(f"current_month_end_{i} = today_{i} + pd.offsets.MonthEnd(0)")
                            lines.append(f"next_month_start_{i} = current_month_end_{i} + timedelta(days=1)")
                            lines.append(f"next_month_end_{i} = next_month_start_{i} + pd.offsets.MonthEnd(0)")
                            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].between(next_month_start_{i}, next_month_end_{i}, inclusive='both')]")
                        elif op == 'is current year':
                            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].dt.year == today_{i}.year]")
                        elif op == 'is previous year':
                            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].dt.year == today_{i}.year - 1]")
                        elif op == 'is next year':
                            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].dt.year == today_{i}.year + 1]")
                    else:
                        date_str = pd.to_datetime(val_cfg).strftime('%Y-%m-%d')
                        lines.append(f"val_dt_{i} = pd.to_datetime('{date_str}')")
                        op_map = {'is exactly': '==', 'is not': '!=', 'is after': '>', 'is on or after': '>=', 'is before': '<', 'is on or before': '<='}
                        lines.append(f"df_filtered = df_filtered[df_filtered['{col}'] {op_map[op]} val_dt_{i}]")
                elif op in ['contains', 'does not contain']:
                    neg = '~' if op == 'does not contain' else ''
                    lines.append(f"df_filtered = df_filtered[{neg}df_filtered['{col}'].astype(str).str.contains(r'''{str(val_cfg)}''', case=False, na=False)]")
                else:
                    val_repr = f"'{str(val_cfg)}'" if isinstance(val_cfg, str) else str(val_cfg)
                    lines.append(f"df_filtered = df_filtered[df_filtered['{col}'] {op} {val_repr}]")
            lines.append("\n# Create Pivot Table")
            vals_code = [it['value_col'] for it in pivot['value_agg_list'] if it['value_col']]
            agg_code = {it['value_col']: it['agg_func'] for it in pivot['value_agg_list'] if it['value_col']}
            lines.append("pivot_params = {")
            lines.append(f"    'index': {pivot['index_cols'] if pivot['index_cols'] else None},")
            lines.append(f"    'columns': {pivot['column_cols'] if pivot['column_cols'] else None},")
            lines.append(f"    'values': {vals_code if vals_code else None},")
            lines.append(f"    'aggfunc': {agg_code if agg_code else 'size'},")
            if pivot['fill_value_enabled']:
                fill_repr = f"'{pivot['custom_fill_value']}'" if isinstance(pivot['custom_fill_value'], str) else pivot['custom_fill_value']
                lines.append(f"    'fill_value': {fill_repr},")
            if pivot['margins_enabled']:
                lines.append("    'margins': True,")
                lines.append(f"    'margins_name': '{pivot['margins_name']}',")
            lines.append("}\n")
            lines.append("pivot_params = {k: v for k, v in pivot_params.items() if not (k in ['index', 'columns', 'values'] and v is None)}\n")
            lines.append("try:")
            lines.append("    pivot_df = pd.pivot_table(df_filtered, **pivot_params)")
            lines.append("    print('Pivot table created successfully.')")
            lines.append("except Exception as e:")
            lines.append("    print(f'Error creating pivot table: {e}')\n")
            pivot['generated_code'] = "\n".join(lines)
            pivot['error_log'] = ''

        if st.sidebar.button("Generate Python Code", key=f"gen_code_{st.session_state.active_pivot}"):
            generate_python_code()

        # --------------------------------------------------
        # Display pivot table and download buttons
        # --------------------------------------------------
        if pivot['pivot_df'] is not None:
            st.subheader(f"Generated Pivot Table [{pivot['name']}]")
            try:
                styled = pivot['pivot_df'].style.background_gradient(axis=None, cmap="BuPu").set_properties(**{'text-align': 'center'})
                st.dataframe(styled)
            except Exception:
                st.dataframe(pivot['pivot_df'].style.set_properties(**{'text-align': 'center'}))

            value_cols = [it['value_col'] for it in pivot['value_agg_list'] if it['value_col']]
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
                    avg_row[col] = sum(vals) / len(vals) if vals else 0
                avg_text = '  '.join([f"<b>Average {c} = {avg_row[c]:.2f}</b>" for c in avg_row])
                st.markdown(f"<div style='text-align:center; font-size:1.2em; margin: 1em 0;'>{avg_text}</div>", unsafe_allow_html=True)

            csv_pivot = pivot['pivot_df'].to_csv().encode('utf-8')
            st.download_button(
                label="Download Pivot Table as CSV",
                data=csv_pivot,
                file_name=f"pivot_{pivot['name'].replace(' ', '_')}.csv",
                mime="text/csv",
            )
            # Hadoop integration for pivot table (optional)
            # with hdfs.open_output_stream(f'/user/your_user/pivot_{pivot['name'].replace(' ', '_')}.csv') as f:
            #     f.write(csv_pivot)

        if pivot.get('generated_code'):
            st.download_button(
                label="Download Generated Python Code",
                data=pivot['generated_code'],
                file_name=f"pivot_code_{pivot['name'].replace(' ', '_')}.py",
                mime="text/x-python",
            )
        if pivot.get('error_log'):
            st.download_button(
                label="Download Error Log",
                data=pivot['error_log'],
                file_name=f"pivot_error_log_{pivot['name'].replace(' ', '_')}.txt",
                mime="text/plain",
            )

        if pivot.get('filtered_df') is not None:
            st.subheader(f"Filtered Data Rows [{pivot['name']}]")
            st.dataframe(pivot['filtered_df'], use_container_width=True)
            filtered_csv = pivot['filtered_df'].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Filtered Data as CSV",
                data=filtered_csv,
                file_name=f"filtered_data_{pivot['name'].replace(' ', '_')}.csv",
                mime="text/csv",
            )

# -------------------------------------------------------------
# Initial message
# -------------------------------------------------------------
if st.session_state.df is None:
    st.info(
        "Welcome to the Interactive Multi-Pivot Table Creator! 🎉\n\n"
        "1. **Upload your CSV file** using the sidebar.\n"
        "2. **Configure your pivots**: Add new pivots, select rows/columns, and define aggregations.\n"
        "3. **View and download** your pivot tables and the generated Python code.\n\n"
        "Use the Extra2 tie option to keep filters consistent across pivots if desired."
    )