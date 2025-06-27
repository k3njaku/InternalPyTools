import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Monthly Performance Report (Fixed Version)")

# 1) Upload
uploaded_file = st.sidebar.file_uploader("Upload your tracker CSV", type=["csv"])
if not uploaded_file:
    st.info("Please upload your tracker CSV to begin.")
    st.stop()

# 2) Load & clean
df = pd.read_csv(uploaded_file, low_memory=False)

# Robust column renaming
rename_map = {}
if "Extra4" in df.columns: rename_map["Extra4"] = "Employee ID new"
if "Extra5" in df.columns: rename_map["Extra5"] = "Name (CNIC)"
if "Extra2" in df.columns: rename_map["Extra2"] = "Department"
df = df.rename(columns=rename_map)

# Check for required columns
required_cols = ["Employee ID new", "Name (CNIC)", "Department", "ScheduledOn", "ScheduledFor", "CreateDt"]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"Missing required columns in your CSV: {missing_cols}")
    st.stop()

# parse dates
for col in ["ScheduledOn", "ScheduledFor", "CreateDt"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# 3) UI controls: project & month
projects = sorted(df["Department"].dropna().unique())
if not projects:
    st.error("No projects found in the 'Department' column.")
    st.stop()
selected_project = st.sidebar.selectbox("Select Project (Extra2)", projects)

# build a list of all year-months present in either date column
all_periods = (
    pd.to_datetime(df[["ScheduledOn","ScheduledFor"]]
                   .stack(), errors="coerce")
      .dt.to_period("M")
      .dropna()
      .unique()
)
period_options = sorted(str(p) for p in all_periods)
if not period_options:
    st.error("No valid periods found in your date columns.")
    st.stop()
selected_period = st.sidebar.selectbox("Select Month (YYYY-MM)", period_options)

# parse YYYY-MM
year, month = map(int, selected_period.split("-"))
start_month = pd.Timestamp(year, month, 1)
end_month   = start_month + pd.offsets.MonthEnd(0)
# previous‐month window for CreateDt
prev_month_end = start_month - pd.Timedelta(days=1)
start_prev     = prev_month_end.replace(day=1)

# 4) filter down to this project & creation‐window
mask = (
    (df["Department"] == selected_project) &
    (df["CreateDt"]      >= start_prev) &
    (df["CreateDt"]      <= end_month)
)
df_proj = df[mask].copy()

# helper: group‐and‐count
def grp_count(df_slice, name):
    return (
      df_slice
        .groupby(["Employee ID new","Name (CNIC)"])
        .size()
        .rename(name)
    )

# 5) compute each metric
# -- Appointments
app_df      = df_proj[df_proj["ScheduledOn"].between(start_month, end_month)]
app_counts  = grp_count(app_df, "Appointments")
avg_app     = app_counts.mean()

# -- Appointments Due
due_df      = df_proj[df_proj["ScheduledFor"].between(start_month, end_month)]
due_counts  = grp_count(due_df, "Appointments Due")

# -- Show up
show_df     = due_df[due_df.get("ShowedUp", pd.Series(["No"]*len(due_df))) == "Yes"]
show_counts = grp_count(show_df, "Show up")
avg_show    = show_counts.mean()

# -- Opportunity
opt_df      = show_df[show_df.get("Opportunity", pd.Series(["No"]*len(show_df))) == "Yes"]
opt_counts  = grp_count(opt_df, "Opportunity")
avg_opt     = opt_counts.mean()

# 6) assemble into one DataFrame
report = (
    pd.concat(
      [app_counts, due_counts, show_counts, opt_counts],
      axis=1
    )
    .fillna(0)
    .reset_index()
)

# 7) add the three team‐average columns
report["Avg team sched"] = avg_app
report["Avg Team held"]  = avg_show
report["Avg Team Opt"]   = avg_opt

# 8) reorder & display exactly as requested
cols = [
  "Employee ID new","Name (CNIC)","Department",
  "Appointments","Avg team sched",
  "Appointments Due","Show up","Avg Team held",
  "Opportunity","Avg Team Opt"
]
missing_report_cols = [col for col in cols if col not in report.columns]
if missing_report_cols:
    st.warning(f"Some columns are missing in the report: {missing_report_cols}")
    # Only show available columns
    cols = [col for col in cols if col in report.columns]

report = report[cols]

st.subheader(f"📊 {selected_project} — {start_month.strftime('%B %Y')}")
st.dataframe(report, use_container_width=True)

# --- Explanation Section ---
with st.expander("ℹ️ How are these numbers calculated?"):
    st.markdown("""
    **Metric Calculation Details:**

    - **Appointments:**  
      Number of rows where `ScheduledOn` is within the selected month, grouped by Employee and Name.

    - **Appointments Due:**  
      Number of rows where `ScheduledFor` is within the selected month, grouped by Employee and Name.

    - **Show up:**  
      Number of rows from *Appointments Due* where `ShowedUp` is `"Yes"`.

    - **Opportunity:**  
      Number of rows from *Show up* where `Opportunity` is `"Yes"`.

    - **Avg team sched / Avg Team held / Avg Team Opt:**  
      These are the averages of the respective metric for all employees in the report.

    **Date Filtering:**
    - The report only includes rows where:
        - `Department` matches your selected project.
        - `CreateDt` is between the first day of the previous month and the end of the selected month.

    **Grouping:**
    - All metrics are grouped by `Employee ID new` and `Name (CNIC)`.

    ---
    *If you have questions about a specific calculation, let us know!*
    """)

# 9) download
csv = report.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download report as CSV",
    data=csv,
    file_name=f"{selected_project}_{selected_period}_report.csv",
    mime="text/csv"
)

st.subheader("🔎 Detailed Calculation Breakdown")

for idx, row in report.iterrows():
    emp_id = row["Employee ID new"]
    emp_name = row["Name (CNIC)"]
    st.markdown(f"---")
    with st.expander(f"Details for {emp_name} ({emp_id})"):
        st.markdown("**Appointments:**")
        app_rows = app_df[(app_df["Employee ID new"] == emp_id) & (app_df["Name (CNIC)"] == emp_name)]
        st.dataframe(app_rows, use_container_width=True)

        st.markdown("**Appointments Due:**")
        due_rows = due_df[(due_df["Employee ID new"] == emp_id) & (due_df["Name (CNIC)"] == emp_name)]
        st.dataframe(due_rows, use_container_width=True)

        st.markdown("**Show up:**")
        show_rows = show_df[(show_df["Employee ID new"] == emp_id) & (show_df["Name (CNIC)"] == emp_name)]
        st.dataframe(show_rows, use_container_width=True)

        st.markdown("**Opportunity:**")
        opt_rows = opt_df[(opt_df["Employee ID new"] == emp_id) & (opt_df["Name (CNIC)"] == emp_name)]
        st.dataframe(opt_rows, use_container_width=True)

        st.markdown("""
        <small>
        <b>How these numbers are calculated:</b><br>
        - <b>Appointments:</b> Count of rows above.<br>
        - <b>Appointments Due:</b> Count of rows above.<br>
        - <b>Show up:</b> Count of rows above.<br>
        - <b>Opportunity:</b> Count of rows above.<br>
        </small>
        """, unsafe_allow_html=True)