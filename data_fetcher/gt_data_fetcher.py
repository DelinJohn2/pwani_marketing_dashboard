import pandas as pd
import streamlit as st
import json
from pathlib import Path
from utils import ensure_str_col
from constants import dc



@st.cache_data(show_spinner="Loading GT & territory …")
def load_gt_terr():
    gt = (
        pd.read_excel(dc.GT_FILE)
        .rename(columns=str.strip)
        .rename(columns={"brand": "Brand", "Markets": "Territory"})
    )
    gt["Territory"] = gt["Territory"].str.title().str.strip()
    gt["Brand"] = gt["Brand"].str.title().str.strip()
    gt["TERR_KEY"] = gt["Territory"]

    terr = json.loads(Path(dc.TERR_GJ).read_text("utf-8"))
    for f in terr["features"]:
        f["properties"]["TERR_KEY"] = f["properties"]["TERRITORY"].title().strip()
    return gt, terr

def load_gt():
    df = pd.read_excel(dc.GT_FILE)
    df = df.rename(
        columns={
            "Markets": "MARKET",
            "SKU_CLUSTER": "CLUSTER",
            "Market_Share": "SHARE_PCT",
            "Total_brand": "SALES_VAL",
            "avg_price": "AVG_PRICE",
            "Sales": "ERP GT Sales Coverage",
        }
    )
    ensure_str_col(df, "MARKET")
    ensure_str_col(df, "CLUSTER")
    ensure_str_col(df, "BRAND", "brand", "Brand")
    ensure_str_col(df, "SKU", "SKU")
    df["SHARE_PCT"] = pd.to_numeric(df["SHARE_PCT"], errors="coerce").fillna(0)
    df["BUBBLE_SIZE"] = (df["SHARE_PCT"] * 100).clip(lower=1) * 20
    df["SHARE_LABEL"] = (df["SHARE_PCT"] * 100).round(1).astype(str) + "%"
    return df.rename(columns={"ERP GT Sales Coverage": "Sales"})