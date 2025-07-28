from constants import dc
import pandas as pd





def load_bubbles():
    df = pd.read_excel(dc.CLUSTER_FILE)
    df.columns = df.columns.str.strip()
    df["County"] = df["County"].astype(str).str.title().str.strip()
    df.rename(
        columns={"brand_qty_1": "Volume", "BRAND": "Brand"},
        inplace=True,
        errors="ignore",
    )
    df["Brand"] = df["Brand"].astype(str).str.title().str.strip()
    df["Cluster"] = df["SKU_CLUSTER"].str.extract(r"^(\w+)", expand=False).str.title()
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)
    return df



def load_comp_text():
    df = pd.read_csv(dc.TEXT_CSV)
    df.columns = df.columns.str.strip()
    df[["Brand", "Competitor", "Territory"]] = df[
        ["Brand", "Competitor", "Territory"]
    ].apply(lambda s: s.astype(str).str.title().str.strip())
    return df
