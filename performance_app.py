# performance_report.py
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Monthly Performance Report")

# 1) Upload
uploaded_file = st.sidebar.file_uploader("Upload your tracker CSV", type=["csv"])
if not uploaded_file:
    st.info("Please upload your tracker CSV to begin.")
    st.stop()

# 2) Load & clean
df = pd.read_csv(uploaded_file, low_memory=False)
# rename the key extras to meaningful names
df = df.rename(columns={
    "Extra4": "Employee ID new",
    "Extra5": "Name (CNIC)",
    "Extra2": "Department"
})
# parse dates
df["ScheduledOn"]   = pd.to_datetime(df["ScheduledOn"],   errors="coerce")
df["ScheduledFor"]  = pd.to_datetime(df["ScheduledFor"],  errors="coerce")
df["CreateDt"]      = pd.to_datetime(df["CreateDt"],      errors="coerce")

# 3) UI controls: project & month
projects = sorted(df["Department"].dropna().unique())
selected_project = st.sidebar.selectbox("Select Project (Extra2)", projects)

# build a list of all year-months present in either date column
all_periods = (
    pd.to_datetime(df[["ScheduledOn","ScheduledFor"]]
                   .stack(), errors="ignore")
      .dt.to_period("M")
      .dropna()
      .unique()
)
period_options = sorted(str(p) for p in all_periods)
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
show_df     = due_df[due_df["ShowedUp"] == "Yes"]
show_counts = grp_count(show_df, "Show up")
avg_show    = show_counts.mean()

# -- Opportunity
opt_df      = show_df[show_df["Opportunity"] == "Yes"]
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
report = report[cols]

st.subheader(f"📊 {selected_project} — {start_month.strftime('%B %Y')}")
st.dataframe(report, use_container_width=True)

# 9) download
csv = report.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download report as CSV",
    data=csv,
    file_name=f"{selected_project}_{selected_period}_report.csv",
    mime="text/csv"
)
