# Workspace Structure

Files listed in .gitignore will be excluded.

## Configuration Files

## File Structure

- 📄 achievers_list.py
  - Imports:
    - import streamlit as st
    - import pandas as pd
    - import datetime.datetime
    - import datetime.timedelta
    - import io
  - Functions:
    - get_known_departments
    - get_department_from_project
    - get_tier_a_target
  - Methods:
    - add_filter
    - remove_filter
- 📄 chiraag_tracker_data_tools.py
  - Imports:
    - import streamlit as st
    - import pandas as pd
    - import requests
    - import json
    - import datetime.date
  - Functions:
    - process_fetched_data
  - Methods:
    - convert_df_to_csv
- 📄 csv_tool.py
  - Imports:
    - import sys
    - import pandas as pd
    - import PySide6.QtWidgets.(
  - Classes:
    - CSVColumnSelector
  - Methods:
    - __init__
    - open_csv_file
    - populate_column_list
    - get_selected_columns_from_list
    - keep_selected_columns
    - remove_selected_columns
    - reset_columns
    - save_csv_file
- 📄 importData.py
  - Imports:
    - import requests
    - import json
    - import csv
  - Methods:
    - flatten_record
- 📄 streamlit_csv_tool.py
  - Imports:
    - import streamlit as st
    - import pandas as pd
  - Methods:
    - convert_df_to_csv
- 📄 streamlit_pivot_tool.py
  - Imports:
    - import streamlit as st
    - import pandas as pd
    - import datetime.datetime
    - import datetime.timedelta
  - Methods:
    - add_value_agg
    - remove_value_agg
    - add_filter
    - remove_filter
