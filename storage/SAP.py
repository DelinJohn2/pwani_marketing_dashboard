"""
spc_dashboard.py  –  SPC dashboard with recipe‑specific ±5 % limits
===================================================================
• Sidebar filters: Year → Month → Date → Shift → Paint Status → recipeCode
• TyreWeight mapping loaded from “Recipe waight data.xlsx”
• USL / LSL = TyreWeight × (1 ± 0.05)
• KPI cards: Cp, Cpk, Pp, Ppk, µ, σ
• Histogram (+1 %, 3 %, 5 %) and X̄ / R charts
"""

from __future__ import annotations
import numpy as np, pandas as pd, urllib.parse as up
from pathlib import Path
import streamlit as st
from sqlalchemy import create_engine, text
from scipy.stats import norm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ────────────────────────── CONFIG


# ---------- Header with logo and title ----------
import base64
from pathlib import Path

logo_path = Path(__file__).parent / "image (4).png"

def img_to_base64(img_path: Path) -> str:
    """Return base64 <str> of an image file."""
    with img_path.open("rb") as f:
        return base64.b64encode(f.read()).decode()

logo_b64 = img_to_base64(logo_path)

st.markdown(
    f"""
    <style>
        .header-flex {{
            display: flex;
            align-items: center;    /* vertical centering */
            gap: 450px;              /* space between logo and text */
            margin-bottom: 12px;    /* push main content down */
        }}
    </style>

    <div class="header-flex">
        <img src="data:image/png;base64,{logo_b64}"
             alt="JK Tyre logo" style="height:104px;">
        <h1 style="margin:10; font-size: 48px;">SPC DASHBOARD</h1><span style="font-size: 16px; font-weight: normal; color: #555;">
            Format No. -BPRO.00-FR.06
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ← insert the header block here →


MAP_FILE = Path(__file__).parent / "Recipe waight data.xlsx"
TB_RECIPE, TB_PAINT = "tbmpcr", "paintingDatanew"

st.set_page_config(layout="wide")
if Path("styles.css").exists():
    st.markdown(f"<style>{Path('styles.css').read_text()}</style>", unsafe_allow_html=True)

# ────────────────────────── 1. load mapping
@st.cache_data(show_spinner=False)
def load_mapping(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]
    need = {"recipeCode", "TyreWeight"}
    if need - set(df.columns):
        st.error(f"Excel must contain columns: {need}"); st.stop()
    df = df[["recipeCode", "TyreWeight"]]
    df["recipeCode"] = df["recipeCode"].str.upper().str.strip()
    return df.dropna()

MAP_DF = load_mapping(MAP_FILE)

# ────────────────────────── 2. engine
@st.cache_resource
def engine():
    odbc = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=10.200.202.124;"
        "DATABASE=SMARTMESBTP;"
        "UID=jkuserBTP;"
        "PWD=jkBTP@474;"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    return create_engine(
        "mssql+pyodbc:///?odbc_connect=" + up.quote_plus(odbc),
        pool_pre_ping=True,
        fast_executemany=True,
    )

ENG = engine()

# ────────────────────────── 3. CTE (Date, Shift, PaintStatus)
BASE_CTE = f"""
WITH data AS (
  SELECT p.dtandTime,
         p.Actual_Weight,
         m.recipecode,
         CONVERT(date, p.dtandTime)          AS TheDate,
         YEAR(p.dtandTime)                   AS YYYY,
         MONTH(p.dtandTime)                  AS MM,
         CASE
           WHEN CAST(p.dtandTime AS time) BETWEEN '07:00' AND '14:59'
                THEN 'Shift-A (07-15)'
           WHEN CAST(p.dtandTime AS time) BETWEEN '15:00' AND '22:59'
                THEN 'Shift-B (15-23)'
           ELSE 'Shift-C (23-07)'
         END                                  AS Shift,
         CASE
           WHEN p.Spray_Status = 1 AND p.Weight_Status = 1 THEN 'Painted'
           WHEN p.Spray_Status = 0 AND p.Weight_Status = 1 THEN 'Not Painted'
           ELSE 'Others'
         END                                  AS PaintStatus
  FROM   {TB_PAINT} p
  LEFT   JOIN {TB_RECIPE} m ON p.barcode = m.gtbarcode
)
"""

# ────────────────────────── 4. helpers
def make_where(flt: dict[str, str]) -> tuple[str, dict]:
    w, p = [], {}
    if flt.get("year")   not in (None, "All"): w.append("YYYY=:y");       p["y"]  = int(flt["year"])
    if flt.get("month")  not in (None, "All"): w.append("MM=:m");         p["m"]  = int(flt["month"])
    if flt.get("date")   not in (None, "All"): w.append("TheDate=:d");    p["d"]  = flt["date"]
    if flt.get("shift")  not in (None, "All"): w.append("Shift=:s");      p["s"]  = flt["shift"]
    if flt.get("paint")  not in (None, "All"): w.append("PaintStatus=:ps");p["ps"] = flt["paint"]
    if flt.get("recipe") not in (None, "All"): w.append("recipecode=:r"); p["r"]  = flt["recipe"]
    return ("WHERE " + " AND ".join(w) if w else ""), p

@st.cache_data(show_spinner=False)
def distinct(col, where_sql, prm):
    sql = BASE_CTE + f"SELECT DISTINCT {col} AS v FROM data {where_sql}"
    return sorted(pd.read_sql(text(sql), ENG, params=prm)["v"].dropna().astype(str))

def dd(label, col, flt, key, fmt=str):
    wsql, prm = make_where(flt)
    opts = ["All"] + [fmt(v) for v in distinct(col, wsql, prm)]
    if key not in st.session_state or st.session_state[key] not in opts:
        st.session_state[key] = "All"
    return st.sidebar.selectbox(label, opts,
                                index=opts.index(st.session_state[key]), key=key)

# ────────────────────────── 5. sidebar filters
flt = {}
st.sidebar.header("🔎 Filters")
flt["year"]   = dd("Year",     "YYYY",       flt, "year",  str)
flt["month"]  = dd("Month",    "MM",         flt, "month", lambda x: f"{int(x):02}")
flt["date"]   = dd("Date",     "TheDate",    flt, "date")
flt["shift"]  = dd("Shift",    "Shift",      flt, "shift")
flt["paint"]  = dd("Paint Status", "PaintStatus", flt, "paint")
flt["recipe"] = dd("Recipecode", "recipecode", flt, "recipe")

batch_size = st.sidebar.number_input("Batch size", 30, 100_000, 150, 30)
sub_n      = st.sidebar.number_input("Sub‑group", 2, 10, 5, 1)

# ────────────────────────── 6. query data
where_sql, prm = make_where(flt)
prm.update(lim=batch_size)

SQL = BASE_CTE + f"""
, num AS (
  SELECT *, ROW_NUMBER() OVER (ORDER BY dtandTime DESC) AS rn
  FROM   data {where_sql}
)
SELECT TOP(:lim) * FROM num ORDER BY rn;
"""
df = pd.read_sql(text(SQL), ENG, params=prm)
if df.empty:
    st.error("No rows match filters."); st.stop()

# merge TyreWeight
df["recipecode"] = df["recipecode"].str.upper().str.strip()
df = df.merge(MAP_DF, left_on="recipecode", right_on="recipeCode", how="left")
df = df.dropna(subset=["TyreWeight"])
if df["recipecode"].nunique() != 1:
    st.error("Select exactly one recipeCode."); st.stop()

target = df["TyreWeight"].iat[0]
USL, LSL = target * 1.05, target * 0.95

# ────────────────────────── 7. SPC statistics
W = df["Actual_Weight"].dropna().to_numpy()
if len(W) < sub_n:
    st.error("Not enough rows."); st.stop()

μ, σ = W.mean(), W.std(ddof=0)
groups = W[:len(W)//sub_n*sub_n].reshape(-1, sub_n)
X̄, R = groups.mean(1), np.ptp(groups, 1)

C = {2:(1.88,0,3.267,1.128),3:(1.023,0,2.574,1.693),4:(0.729,0,2.282,2.059),
     5:(0.577,0,2.114,2.326),6:(0.483,0,2.004,2.534),7:(0.419,0.076,1.924,2.704),
     8:(0.373,0.136,1.864,2.847),9:(0.337,0.184,1.816,2.970),10:(0.308,0.223,1.777,3.078)}
A2, D3, D4, d2 = C[sub_n]
Xbar̄, R̄ = X̄.mean(), R.mean()
UCLx, LCLx = Xbar̄ + A2*R̄, Xbar̄ - A2*R̄
UCLr, LCLr = D4*R̄,       D3*R̄

σ_short = R̄ / d2
Cp  = (USL - LSL) / (6 * σ_short)
Cpk = min(USL - μ, μ - LSL) / (3 * σ_short)
Pp  = (USL - LSL) / (6 * σ)
Ppk = min(USL - μ, μ - LSL) / (3 * σ)

# ────────────────────────── 8. KPI cards

labels = ["Cp", "Cpk", "Pp", "Ppk", "Mean µ", "σ overall"]
vals   = [Cp, Cpk, Pp, Ppk, μ, σ]
bgs    = "#e8f5e9 #fff3e0 #e3f2fd #fce4ec #ede7f6 #f3e5f5".split()
for i, (c, l, v) in enumerate(zip(st.columns(6), labels, vals)):
    c.markdown(
        f"<div style='background:{bgs[i]};padding:18px;border-radius:12px;text-align:center'>"
        f"<h4>{l}</h4><p style='font-size:28px'>{v:.2f}</p></div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top:30px;'></div>", unsafe_allow_html=True)

# ────────────────────────── 9. charts
left, right = st.columns([1.7, 1], gap="large")

# Histogram
with left:
    xx = np.linspace(W.min(), W.max(), 300)
    fig_h = go.Figure([
        go.Histogram(x=W, nbinsx=40, histnorm="probability density",
                     marker_color="#4E79A7", opacity=0.85),
        go.Scatter(x=xx, y=norm.pdf(xx, μ, σ),
                   line=dict(width=2, color="#E15759"), name="Normal Fit")
    ])

    # Add LSL and USL lines
    fig_h.add_vline(LSL, line=dict(color="#BF0000", width=2), annotation_text="LSL")
    fig_h.add_vline(USL, line=dict(color="#BF0000", width=2), annotation_text="USL")

    # Add tolerance zones
    fig_h.add_vrect(x0=target*0.97, x1=target*1.03,  # ±3% zone
                    fillcolor="yellow", opacity=0.2, layer="below", line_width=0,
                    annotation_text="±3%")
    
    fig_h.add_vrect(x0=target*0.99, x1=target*1.01,  # ±1% zone
                    fillcolor="green", opacity=0.2, layer="below", line_width=0,
                    annotation_text="±1%")
    
    # Beyond ±3% → Red zones
    fig_h.add_vrect(x0=LSL, x1=target*0.97,
                    fillcolor="red", opacity=0.2, layer="below", line_width=0,
                    annotation_text="±5%")
    fig_h.add_vrect(x0=target*1.03, x1=USL,
                    fillcolor="red", opacity=0.2, layer="below", line_width=0,
                    annotation_text="±5")

    fig_h.update_yaxes(range=[0, None]) 

    # Update layout
    fig_h.update_layout(template="plotly_white", title="Capability Histogram",
                        height=440, bargap=0.03,
                        margin=dict(l=60, r=20, t=60, b=60),
                        xaxis=dict(title="Weight", ticks="outside", ticklen=6, tickcolor="#999"),
                        yaxis=dict(title="Density", ticks="outside", ticklen=6, tickcolor="#999"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    st.plotly_chart(fig_h, use_container_width=True)

# X̄ & R
with right:
    idx = np.arange(1, len(X̄)+1)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("X̄ Chart", "R Chart"))
    # X̄
    fig.add_scatter(x=idx, y=X̄, mode="lines+markers", line=dict(width=2),
                    marker=dict(size=6), row=1, col=1)
    for y, colr, lab in [(UCLx, "#BF0000", "UCLx"), (LCLx, "#BF0000", "LCLx"),
                         (Xbar̄, "green", "X̄‾")]:
        fig.add_hline(y, line=dict(color=colr, dash="dash"),
                      annotation_text=lab, annotation_position="top left",
                      row=1, col=1)
    # R
    fig.add_scatter(x=idx, y=R, mode="lines+markers",
                    line=dict(width=2, color="#59A14F"),
                    marker=dict(size=6, color="#59A14F"), row=2, col=1)
    for y, colr, lab in [(UCLr, "#BF0000", "UCLr"),
                         (LCLr, "#BF0000", "LCLr"),
                         (R̄, "green", "R‾")]:
        fig.add_hline(y, line=dict(color=colr, dash="dash"),
                      annotation_text=lab, annotation_position="top left",
                      row=2, col=1)
    fig.update_layout(template="plotly_white", height=440, showlegend=False,
                      margin=dict(l=60, r=20, t=50, b=60),
                      xaxis2=dict(title="Sub‑group index", ticks="outside",
                                  ticklen=6, tickcolor="#999"),
                      yaxis=dict(title="Mean", ticks="outside", ticklen=6, tickcolor="#999"),
                      yaxis2=dict(title="Range", ticks="outside", ticklen=6, tickcolor="#999"))
    st.plotly_chart(fig, use_container_width=True)

# ────────────────────────── 10. data & download
with st.expander("Latest rows"):
    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", df.to_csv(index=False).encode(),
                       file_name="latest.csv", mime="text/csv")
