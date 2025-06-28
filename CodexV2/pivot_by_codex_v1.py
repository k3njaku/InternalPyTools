import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Interactive Multi-Pivot Table Creator (Codex Edition)")

SAVED_VIEWS_FILE = 'saved_pivot_views.json'

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def load_csv(file):
    """Load CSV and try to parse date columns."""
    df = pd.read_csv(file)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].replace('0000-00-00', pd.NA)
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except Exception:
                pass
    return df


def default_pivot_config(df):
    """Return a new empty pivot configuration."""
    return {
        'name': f"Pivot {len(st.session_state.multi_pivots)+1}",
        'index_cols': [],
        'column_cols': [],
        'value_agg_list': [],
        'filters': [],
        'fill_value_enabled': False,
        'custom_fill_value': None,
        'margins_enabled': False,
        'margins_name': 'All_Totals',
        'pivot_df': None,
        'last_error': None,
        'generated_code': None,
        'error_log': ''
    }


def serialize_dates(obj):
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_dates(v) for v in obj]
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    return obj


def save_views():
    with open(SAVED_VIEWS_FILE, 'w') as f:
        json.dump([serialize_dates({k: v for k, v in p.items() if k != 'pivot_df'})
                   for p in st.session_state.multi_pivots], f, indent=2)


def load_views():
    try:
        with open(SAVED_VIEWS_FILE, 'r') as f:
            loaded = json.load(f)
        for p in loaded:
            p['pivot_df'] = None
        st.session_state.multi_pivots = loaded
        st.session_state.active_pivot = 0
    except Exception:
        st.warning("Failed to load saved views")


def apply_filters(df, filters):
    """Apply list of filter configurations to DataFrame."""
    filtered_df = df.copy()
    for f_conf in filters:
        if not f_conf.get('column'):
            continue
        col = f_conf['column']
        op = f_conf['operator']
        val = f_conf['value']
        try:
            is_date = op in [
                "is exactly", "is not", "is after", "is on or after",
                "is before", "is on or before", "is between (inclusive)",
                "is current month", "is previous month", "is next month",
                "is current year", "is previous year", "is next year"
            ]
            col_data = filtered_df[col]
            if is_date:
                col_dt = pd.to_datetime(col_data, errors='coerce')
                valid_mask = col_dt.notna()
                if pd.api.types.is_datetime64_any_dtype(col_data):
                    valid_mask = valid_mask | col_data.isna()
                filtered_df = filtered_df[valid_mask]
                col_dt = col_dt[valid_mask]
            if op == "is between (inclusive)" and is_date:
                start, end = pd.to_datetime(val[0]), pd.to_datetime(val[1])
                filtered_df = filtered_df[col_dt.between(start, end)]
            elif is_date:
                today = pd.Timestamp.now().normalize()
                if op == "is current month":
                    filtered_df = filtered_df[(col_dt.dt.year == today.year) & (col_dt.dt.month == today.month)]
                elif op == "is previous month":
                    start_month = today.replace(day=1)
                    end_prev = start_month - timedelta(days=1)
                    start_prev = end_prev.replace(day=1)
                    filtered_df = filtered_df[col_dt.between(start_prev, end_prev, inclusive="both")]
                elif op == "is next month":
                    end_month = today + pd.offsets.MonthEnd(0)
                    start_next = end_month + timedelta(days=1)
                    end_next = start_next + pd.offsets.MonthEnd(0)
                    filtered_df = filtered_df[col_dt.between(start_next, end_next, inclusive="both")]
                elif op == "is current year":
                    filtered_df = filtered_df[col_dt.dt.year == today.year]
                elif op == "is previous year":
                    filtered_df = filtered_df[col_dt.dt.year == today.year - 1]
                elif op == "is next year":
                    filtered_df = filtered_df[col_dt.dt.year == today.year + 1]
                else:
                    val_dt = pd.to_datetime(val)
                    op_map = {
                        "is exactly": col_dt == val_dt,
                        "is not": col_dt != val_dt,
                        "is after": col_dt > val_dt,
                        "is on or after": col_dt >= val_dt,
                        "is before": col_dt < val_dt,
                        "is on or before": col_dt <= val_dt,
                    }
                    filtered_df = filtered_df[op_map[op]]
            else:
                if op in ["contains", "does not contain"]:
                    comp = col_data.astype(str).str.contains(str(val), case=False, na=False)
                    filtered_df = filtered_df[comp if op == "contains" else ~comp]
                else:
                    comp_val = pd.to_numeric(val, errors='ignore') if pd.api.types.is_numeric_dtype(col_data) else val
                    ops = {
                        "==": col_data == comp_val,
                        "!=": col_data != comp_val,
                        ">": col_data > comp_val,
                        "<": col_data < comp_val,
                        ">=": col_data >= comp_val,
                        "<=": col_data <= comp_val
                    }
                    filtered_df = filtered_df[ops.get(op, col_data == comp_val)]
        except Exception as e:
            st.sidebar.warning(f"Filter on {col} failed: {e}")
    return filtered_df


def create_pivot(df, cfg):
    value_cols = [v['value_col'] for v in cfg['value_agg_list'] if v['value_col']]
    agg_dict = {v['value_col']: v['agg_func'] for v in cfg['value_agg_list'] if v['value_col']}
    params = {
        'index': cfg['index_cols'] or None,
        'columns': cfg['column_cols'] or None,
        'values': value_cols or None,
        'aggfunc': agg_dict or 'size'
    }
    if cfg['fill_value_enabled']:
        params['fill_value'] = cfg['custom_fill_value']
    if cfg['margins_enabled']:
        params['margins'] = True
        params['margins_name'] = cfg['margins_name']
    params = {k: v for k, v in params.items() if v is not None or k in ['fill_value', 'margins', 'margins_name']}
    return pd.pivot_table(df, **params)


def generate_code(cfg):
    """Create python code representing the pivot configuration."""
    lines = [
        "import pandas as pd",
        "from datetime import datetime, timedelta",
        "\n# df_original = pd.read_csv('your_file.csv')",
        "df_filtered = df_original.copy()\n"
    ]
    for i, f_conf in enumerate(cfg['filters']):
        col = f_conf['column']
        op = f_conf['operator']
        val = f_conf['value']
        if not col:
            continue
        is_date = op in [
            "is exactly", "is not", "is after", "is on or after",
            "is before", "is on or before", "is between (inclusive)",
            "is current month", "is previous month", "is next month",
            "is current year", "is previous year", "is next year"
        ]
        if is_date:
            lines.append(f"df_filtered['{col}'] = pd.to_datetime(df_filtered['{col}'], errors='coerce')")
            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].notna()]")
        if op == "is between (inclusive)" and is_date:
            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'].between(pd.to_datetime('{val[0]}'), pd.to_datetime('{val[1]}'))]")
        elif op in ["contains", "does not contain"]:
            neg = "~" if op == "does not contain" else ""
            lines.append(f"df_filtered = df_filtered[{neg}df_filtered['{col}'].astype(str).str.contains(r'''{val}''', case=False, na=False)]")
        elif is_date:
            op_map = {
                "is exactly": "==",
                "is not": "!=",
                "is after": ">",
                "is on or after": ">=",
                "is before": "<",
                "is on or before": "<=",
            }
            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'] {op_map[op]} pd.to_datetime('{val}')]")
        else:
            lines.append(f"df_filtered = df_filtered[df_filtered['{col}'] {op} {repr(val)}]")
    val_cols = [v['value_col'] for v in cfg['value_agg_list'] if v['value_col']]
    agg_dict = {v['value_col']: v['agg_func'] for v in cfg['value_agg_list'] if v['value_col']}
    lines.append("\npivot_df = pd.pivot_table(df_filtered,")
    lines.append(f"    index={cfg['index_cols'] or None},")
    lines.append(f"    columns={cfg['column_cols'] or None},")
    lines.append(f"    values={val_cols or None},")
    lines.append(f"    aggfunc={agg_dict or 'size'},")
    if cfg['fill_value_enabled']:
        lines.append(f"    fill_value={repr(cfg['custom_fill_value'])},")
    if cfg['margins_enabled']:
        lines.append("    margins=True,")
        lines.append(f"    margins_name='{cfg['margins_name']}',")
    lines.append(")")
    return "\n".join(lines)

# ---------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------

if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'multi_pivots' not in st.session_state:
    st.session_state.multi_pivots = []
if 'active_pivot' not in st.session_state:
    st.session_state.active_pivot = 0

# ---------------------------------------------------------------------
# File Upload & Global Actions
# ---------------------------------------------------------------------

uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    if st.session_state.uploaded_file_name != uploaded_file.name:
        st.session_state.df = load_csv(uploaded_file)
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.multi_pivots = []
        st.session_state.active_pivot = 0
else:
    st.session_state.df = None
    st.session_state.uploaded_file_name = None
    st.session_state.multi_pivots = []
    st.session_state.active_pivot = 0

if st.sidebar.button("Save All Views"):
    save_views()
if st.sidebar.button("Load Saved Views"):
    load_views()

# ---------------------------------------------------------------------
# Show Full Data
# ---------------------------------------------------------------------
if st.session_state.df is not None:
    st.subheader("All Data Rows")
    st.dataframe(st.session_state.df, use_container_width=True)
    csv_all = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("Download All Data Rows", csv_all, "all_data.csv", "text/csv")
    st.divider()

# ---------------------------------------------------------------------
# Pivot Management
# ---------------------------------------------------------------------
if st.session_state.df is not None:
    st.sidebar.markdown("## Manage Pivots")
    if st.sidebar.button("Add New Pivot"):
        st.session_state.multi_pivots.append(default_pivot_config(st.session_state.df))
        st.session_state.active_pivot = len(st.session_state.multi_pivots)-1
    if st.session_state.multi_pivots:
        names = [p['name'] for p in st.session_state.multi_pivots]
        st.session_state.active_pivot = st.sidebar.selectbox(
            "Select Pivot",
            options=list(range(len(names))),
            format_func=lambda i: names[i],
            index=min(st.session_state.active_pivot, len(names)-1)
        )
        if st.sidebar.button("Remove Selected Pivot"):
            st.session_state.multi_pivots.pop(st.session_state.active_pivot)
            st.session_state.active_pivot = max(0, st.session_state.active_pivot-1)

if st.session_state.df is not None and st.session_state.multi_pivots:
    show_all = st.sidebar.checkbox("Show all pivots", value=False)

    # tie Extra2 filter across pivots
    extra2_indices = []
    for idx, pv in enumerate(st.session_state.multi_pivots):
        for fidx, f in enumerate(pv.get('filters', [])):
            if f.get('column') == 'Extra2':
                extra2_indices.append((idx, fidx))
    tie_extra2 = False
    if len(extra2_indices) > 1:
        tie_extra2 = st.sidebar.checkbox("Tie Extra2 filter across pivots", value=False)
        if tie_extra2:
            shared_val = None
            for idx, fidx in extra2_indices:
                val = st.session_state.multi_pivots[idx]['filters'][fidx].get('value')
                if val:
                    shared_val = val
                    break
            if shared_val is not None:
                for idx, fidx in extra2_indices:
                    st.session_state.multi_pivots[idx]['filters'][fidx]['value'] = shared_val

    if show_all:
        for pv in st.session_state.multi_pivots:
            st.markdown(f"### Pivot Table: {pv['name']}")
            if pv['pivot_df'] is not None:
                st.dataframe(pv['pivot_df'].style.background_gradient(axis=None, cmap="BuPu"))
            else:
                st.info("No pivot generated yet")
        st.stop()

    pivot = st.session_state.multi_pivots[st.session_state.active_pivot]
    df_source = st.session_state.df.copy()
    cols = df_source.columns.tolist()

    st.sidebar.header(f"Pivot Config [{pivot['name']}]")
    pivot['name'] = st.sidebar.text_input("Pivot Name", value=pivot['name'])
    pivot['index_cols'] = st.sidebar.multiselect("Rows", options=cols, default=pivot['index_cols'])
    pivot['column_cols'] = st.sidebar.multiselect("Columns", options=cols, default=pivot['column_cols'])

    agg_functions = {
        "Sum": "sum",
        "Mean": "mean",
        "Median": "median",
        "Min": "min",
        "Max": "max",
        "Count": "count",
        "Size": "size",
        "Std": "std",
        "Var": "var",
        "Nunique": "nunique"
    }

    if 'value_agg_list' not in pivot:
        pivot['value_agg_list'] = []

    def add_val_agg():
        pivot['value_agg_list'].append({'value_col': None, 'agg_func': 'sum'})
    def remove_val_agg(i):
        if 0 <= i < len(pivot['value_agg_list']):
            pivot['value_agg_list'].pop(i)

    for i, item in enumerate(pivot['value_agg_list']):
        c1, c2, c3 = st.sidebar.columns([3,3,1])
        with c1:
            item['value_col'] = st.selectbox(
                f"Value Column {i+1}", [None] + cols,
                index=([None] + cols).index(item['value_col']) if item['value_col'] in ([None] + cols) else 0,
                key=f"valcol_{i}")
        with c2:
            agg_name = next((k for k,v in agg_functions.items() if v == item['agg_func']), 'Sum')
            sel = st.selectbox(
                f"Aggregation {i+1}", list(agg_functions.keys()),
                index=list(agg_functions.keys()).index(agg_name), key=f"agg_{i}")
            item['agg_func'] = agg_functions[sel]
        with c3:
            st.button("➖", key=f"remove_val_{i}", on_click=remove_val_agg, args=(i,))
    st.sidebar.button("Add Value/Aggregation", on_click=add_val_agg)

    # Filters
    if 'filters' not in pivot:
        pivot['filters'] = []

    def add_filter():
        pivot['filters'].append({'column': None, 'operator': '==', 'value': ''})
    def remove_filter(i):
        if 0 <= i < len(pivot['filters']):
            pivot['filters'].pop(i)

    for i, f in enumerate(pivot['filters']):
        c1, c2, c3, c4 = st.sidebar.columns([3,2,3,1])
        f['column'] = c1.selectbox(
            f"Filter Column {i+1}", [None] + cols,
            index=([None]+cols).index(f['column']) if f['column'] in ([None]+cols) else 0,
            key=f"fcol_{i}")
        if f['column'] == 'Extra2':
            projects = sorted(df_source['Extra2'].dropna().unique().tolist())
            f['value'] = c3.selectbox(
                f"Project {i+1}", projects,
                index=projects.index(f['value']) if f['value'] in projects else 0,
                key=f"fval_{i}")
            f['operator'] = '=='
            c2.markdown('=')
        else:
            selected_col = f['column']
            ops = ["==","!=","contains","does not contain"]
            is_date = False
            if selected_col and selected_col in df_source.columns:
                try:
                    if pd.api.types.is_datetime64_any_dtype(df_source[selected_col]):
                        is_date = True
                    else:
                        sample = df_source[selected_col].dropna().iloc[:5]
                        if not sample.empty and pd.to_datetime(sample, errors='coerce').notna().all():
                            is_date = True
                except Exception:
                    is_date = False
                if is_date:
                    ops = ["is exactly","is not","is after","is on or after","is before","is on or before","is between (inclusive)","is current month","is previous month","is next month","is current year","is previous year","is next year"]
                elif pd.api.types.is_numeric_dtype(df_source[selected_col]):
                    ops = ["==","!=",">","<",">=","<="]
            f['operator'] = c2.selectbox(
                f"Operator {i+1}", ops,
                index=ops.index(f['operator']) if f['operator'] in ops else 0,
                key=f"fop_{i}")
            if is_date and f['operator'] == 'is between (inclusive)':
                if not isinstance(f['value'], list) or len(f['value']) != 2:
                    f['value'] = [df_source[selected_col].min(), df_source[selected_col].max()]
                f['value'][0] = c3.date_input("Start", value=pd.to_datetime(f['value'][0]), key=f"fval_s_{i}")
                f['value'][1] = c3.date_input("End", value=pd.to_datetime(f['value'][1]), key=f"fval_e_{i}")
            elif is_date and f['operator'] in ["is exactly","is not","is after","is on or after","is before","is on or before"]:
                default = pd.to_datetime(f['value'], errors='coerce')
                if pd.isna(default):
                    default = datetime.now().date()
                f['value'] = c3.date_input("Date", value=default, key=f"fval_d_{i}")
            elif is_date and f['operator'] in ["is current month","is previous month","is next month","is current year","is previous year","is next year"]:
                c3.markdown(f"*{f['operator']}*")
                f['value'] = None
            elif selected_col and pd.api.types.is_numeric_dtype(df_source[selected_col]):
                f['value'] = c3.number_input("Value", value=pd.to_numeric(f['value'], errors='coerce') if f['value'] != '' else 0, key=f"fval_n_{i}")
            elif selected_col and (pd.api.types.is_categorical_dtype(df_source[selected_col]) or df_source[selected_col].nunique() < 20):
                vals = [''] + df_source[selected_col].dropna().unique().tolist()
                f['value'] = c3.selectbox("Value", vals, index=vals.index(f['value']) if f['value'] in vals else 0, key=f"fval_c_{i}")
            else:
                f['value'] = c3.text_input("Value", value=str(f['value']), key=f"fval_t_{i}")
            c4.button("➖", key=f"rmfilter_{i}", on_click=remove_filter, args=(i,))
    st.sidebar.button("Add Filter", on_click=add_filter)

    pivot['fill_value_enabled'] = st.sidebar.checkbox("Fill missing values", value=pivot['fill_value_enabled'])
    if pivot['fill_value_enabled']:
        val_str = st.sidebar.text_input("Fill value", value=str(pivot['custom_fill_value'] if pivot['custom_fill_value'] is not None else '0'))
        try:
            pivot['custom_fill_value'] = float(val_str)
            if pivot['custom_fill_value'].is_integer():
                pivot['custom_fill_value'] = int(pivot['custom_fill_value'])
        except ValueError:
            pivot['custom_fill_value'] = val_str
    pivot['margins_enabled'] = st.sidebar.checkbox("Show totals row/col", value=pivot['margins_enabled'])
    if pivot['margins_enabled']:
        pivot['margins_name'] = st.sidebar.text_input("Totals label", value=pivot['margins_name'])

    if st.sidebar.button("Create Pivot Table"):
        filtered = apply_filters(df_source, pivot['filters'])
        try:
            pivot['pivot_df'] = create_pivot(filtered, pivot)
            pivot['last_error'] = None
        except Exception as e:
            pivot['pivot_df'] = None
            pivot['last_error'] = str(e)
            pivot['error_log'] += str(e) + "\n"

    if st.sidebar.button("Generate Python Code"):
        pivot['generated_code'] = generate_code(pivot)

    if pivot['pivot_df'] is not None:
        st.subheader(f"Pivot Table: {pivot['name']}")
        styled = pivot['pivot_df'].style.background_gradient(axis=None, cmap="BuPu").set_properties(**{'text-align': 'center'})
        st.dataframe(styled)
        csv_data = pivot['pivot_df'].to_csv().encode('utf-8')
        st.download_button(
            f"Download {pivot['name']} as CSV",
            csv_data,
            f"pivot_{pivot['name'].replace(' ','_')}.csv",
            "text/csv"
        )
        if pivot['generated_code']:
            st.download_button(
                "Download Python Code",
                pivot['generated_code'],
                f"pivot_code_{pivot['name'].replace(' ','_')}.py",
                "text/x-python"
            )
        if pivot['error_log']:
            st.download_button(
                "Download Error Log",
                pivot['error_log'],
                f"pivot_error_log_{pivot['name'].replace(' ','_')}.txt",
                "text/plain"
            )
    elif pivot.get('last_error'):
        st.error(pivot['last_error'])
else:
    st.info("Please upload a CSV file to begin.")
