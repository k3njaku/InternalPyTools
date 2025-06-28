# Repository Overview

This repository contains various Streamlit tools and helper scripts for working with appointment data, CSV manipulation and pivot tables. Many of the files are earlier versions or experimentation copies.

## Main Utilities
- **achievers_list.py** – Streamlit app for displaying department targets and calculating metrics.
- **chiraag_tracker_data_tools.py** – Fetches and processes appointment data from a remote service.
- **csv_tool.py** – PySide6 desktop GUI to select and export CSV columns.
- **importData.py** – Script to download appointment data via HTTP and save it as CSV.
- **performance_app.py** / **performance_app_fixed.py** – Streamlit dashboards for monthly performance reporting (the _fixed_ version is the latest).
- **pivot_tool.py** and **pivottools_v2.py** – Interactive multi‑pivot table creators written in Streamlit.
- **streamlit_* files** – Miscellaneous Streamlit utilities for filtering, cleaning and formatting CSV files.

## Duplicates
There are several copies of similar scripts (e.g. multiple `CHT_Data_Viewer` versions, `performance_app` vs `performance_app_fixed`, two pivot tool implementations). These represent iterations where later files are generally more polished.

## Data
The repository includes some CSV files used for testing and `saved_pivot_views.json` for persisting pivot configurations.

## Suggestion_by_Codex
This directory contains the new `pivot_tool_perfect.py`, which consolidates features from both pivot tool versions and lets you download filtered datasets beneath each pivot table, along with this overview file.

## Codexv2
Contains `pivot_by_codex_v6.py`, a further refinement that allows copying filter settings from the active pivot to other pivots or to a newly created pivot.
