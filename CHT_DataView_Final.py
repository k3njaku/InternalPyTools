# cht_viewer.py
import os, json, base64, importlib, requests, datetime
import streamlit as st, pandas as pd
from rapidfuzz import fuzz
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# ───────────────────────────── CONSTANTS ────────────────────────────────────
MEDIA_PREFIX    = "https://apptrack.chiraagtracker.com/"
MOD_SUFFIX      = "_modified.csv"
OPT_FILE        = "checked_for_options.json"
VALID_OPTS      = ["Approved", "Rejected", "Hold"]

# ───────────────────────────── STREAMLIT PAGE ───────────────────────────────
st.set_page_config(layout="wide")
st.title("CHT Data Viewer — solid, no-cache edition")

# ───────────────────────────── OPTION STORAGE ───────────────────────────────
def load_checked_opts():
    if os.path.isfile(OPT_FILE):
        return json.load(open(OPT_FILE))
    default = ["Audio OK", "Video OK", "PDF OK", "Other"]
    json.dump(default, open(OPT_FILE,"w"), indent=2); return default
ALL_OPTS = load_checked_opts()

# ───────────────────────────── CSV LOAD / SAVE ──────────────────────────────
def load_csv(path:str)->pd.DataFrame:
    df = pd.read_csv(path)
    for col in ("Checked For","Validation","Comments"):
        if col not in df.columns: df[col] = ""
    return df

def save_csv(df:pd.DataFrame, orig_path:str):
    new_path = orig_path.replace(".csv", MOD_SUFFIX)
    df.to_csv(new_path, index=False)
    return new_path

# ───────────────────────────── PDF PREVIEW ───────────────────────────────────
def show_pdf(url:str,height:int=700):
    if importlib.util.find_spec("streamlit_pdf_viewer"):
        from streamlit_pdf_viewer import pdf_viewer
        pdf_viewer(requests.get(url).content, width="100%", height=height); return
    url += "#view=FitH"
    st.components.v1.html(
        f"""<style>.wrap{{position:relative;height:100vh}}
        iframe{{position:absolute;width:100%;height:100%;border:none}}</style>
        <div class="wrap"><iframe src="{url}"></iframe></div>""",
        height=height
    )

# ───────────────────────────── MEDIA DETECT ─────────────────────────────────
def media_tuple(val):
    if not isinstance(val,str): return None
    url = val if val.lower().startswith(("http://","https://")) else \
          MEDIA_PREFIX+val if val.lower().startswith("assets/") else None
    if not url: return None
    ext=url.split("?")[0].rsplit(".",1)[-1].lower()
    cat = ("image" if ext in {"png","jpg","jpeg","gif","bmp","webp"} else
           "video" if ext in {"mp4","webm","mov","avi"}               else
           "audio" if ext in {"mp3","wav","ogg","m4a"}                else
           "pdf"   if ext=="pdf"                                      else "other")
    return cat,url

def fuzzy(series,q,th=60):
    return sorted([(c,v,s) for c,v in series.items()
                   if (s:=max(fuzz.token_set_ratio(q,c),
                               fuzz.token_set_ratio(q,str(v))))>=th],
                  key=lambda x:x[2], reverse=True)

# ───────────────────────────── FILE UPLOAD ──────────────────────────────────
up = st.file_uploader("Upload CSV", type=["csv"])
if not up: st.stop()

orig_path = os.path.join(".", up.name)
with open(orig_path,"wb") as f: f.write(up.getbuffer())
use_path  = orig_path.replace(".csv", MOD_SUFFIX) if os.path.exists(
           orig_path.replace(".csv", MOD_SUFFIX)) else orig_path
df = load_csv(use_path)

# ───────────────────────────── MODE PICKER ───────────────────────────────────
mode = st.radio("Mode",["Explore (sheet)","Search"])
sel_idx = None

if mode.startswith("Explore"):
    grid_df = df.reset_index()
    gb = GridOptionsBuilder.from_dataframe(grid_df)
    gb.configure_default_column(filter=True, floatingFilter=True, sortable=True)
    gb.configure_selection("single")
    resp = AgGrid(grid_df, gridOptions=gb.build(),
                  update_mode=GridUpdateMode.SELECTION_CHANGED,
                  data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                  height=350, fit_columns_on_grid_load=True)
    rows = resp["selected_rows"]
    if rows: sel_idx = rows[0]["index"]
else:
    q = st.text_input("Search")
    if q:
        mask = df.apply(lambda r: r.astype(str).str.contains(q,case=False,na=False).any(), axis=1)
        hits = df[mask].head(7)
        if hits.empty: st.warning("No matches"); st.stop()
        opts={i:f"{r.Extra2} | {r.CompanyName} | {r.ProspectName}" for i,r in hits.iterrows()}
        sel_idx = st.radio("Pick row", list(opts), format_func=lambda i:f"Row {i}: {opts[i]}")

if sel_idx is None: st.info("Select a row"); st.stop()

# ───────────────────────────── SHOW ROW / MEDIA / REVIEW ────────────────────
row = df.loc[sel_idx]
st.subheader(f"Row {sel_idx}")
st.dataframe(row.to_frame().T,use_container_width=True)

# fuzzy
fuzzy_q = st.text_input("Fuzzy search this row")
if fuzzy_q:
    hits = fuzzy(row,fuzzy_q)
    if hits: [st.write(f"· **{c}**: {v} ({s})") for c,v,s in hits]
    else: st.info("No fuzzy hits")

# media
med = [m for m in map(media_tuple,row.values) if m]
if med:
    st.subheader("Media")
    for kind,url in med:
        if kind=="image": st.image(url,use_container_width=True)
        elif kind=="video": st.video(url)
        elif kind=="audio": st.audio(url)
        elif kind=="pdf": show_pdf(url)
        else: st.markdown(f"[Download]({url})")
else: st.info("No media")

# review form
st.markdown("---")
with st.form(key="review"):
    cols = st.columns(3)
    cf   = cols[0].selectbox("Checked For", ALL_OPTS,
              index=ALL_OPTS.index(row["Checked For"])
                    if row["Checked For"] in ALL_OPTS else 0)
    val  = cols[1].selectbox("Validation",VALID_OPTS,
              index=VALID_OPTS.index(row["Validation"])
                    if row["Validation"] in VALID_OPTS else 0)
    cm   = cols[2].text_area("Comments", row["Comments"] or "", height=120)
    add_opt = st.text_input("Add new 'Checked For' option")
    submitted = st.form_submit_button("Save changes")

if add_opt:
    if add_opt not in ALL_OPTS:
        ALL_OPTS.append(add_opt); json.dump(ALL_OPTS, open(OPT_FILE,"w"), indent=2)
        st.success(f"Added option {add_opt} – reload to use")
if submitted:
    df.loc[sel_idx, ["Checked For","Validation","Comments"]] = cf, val, cm
    save_csv(df, orig_path)
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.success(f"Saved to disk ({ts}) ✔")
