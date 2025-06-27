import pandas as pd
from datetime import datetime, timedelta # Import if using date operations

# 1. Load your DataFrame (replace with your actual data loading)
# Example: df_original = pd.read_csv('your_file.csv')
df_original = pd.DataFrame() # Placeholder - ensure this is your actual DataFrame

df_filtered = df_original.copy()

# 2. Apply Filters
df_filtered = df_filtered[df_filtered['ScheduledOn'].astype(str).str.contains(r'''-05-''', case=False, na=False)]
df_filtered['CreateDt'] = pd.to_datetime(df_filtered['CreateDt'], errors='coerce')
df_filtered = df_filtered[df_filtered['CreateDt'].notna()] # Remove rows where date conversion failed
start_date_1 = pd.to_datetime('2025-04-01')
end_date_1 = pd.to_datetime('2025-05-31')
df_filtered = df_filtered[df_filtered['CreateDt'].between(start_date_1, end_date_1, inclusive='both')]
df_filtered = df_filtered[df_filtered['Extra2'] == 'Avibra']

# 3. Create Pivot Table
pivot_params = {
    'index': ['Extra5'],
    'columns': None,
    'values': ['CompanyName'],
    'aggfunc': {'CompanyName': 'count'},
}

# Remove None params for pandas pivot_table call if they were None initially
pivot_params = {k: v for k, v in pivot_params.items() if not (k in ['index', 'columns', 'values'] and v is None)}

try:
    pivot_df = pd.pivot_table(df_filtered, **pivot_params)
    print('Pivot table created successfully.')
    # print(pivot_df)
except Exception as e:
    print(f'Error creating pivot table: {e}')
