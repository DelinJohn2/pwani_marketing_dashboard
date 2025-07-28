import pandas as pd
from constants import dc 




def load_mt():
    df = pd.read_excel(dc.MT_FILE)
    df.columns = df.columns.str.strip()
    df["County"] = df["County"].astype(str).str.title().str.strip()
    df.rename(columns={"BRAND": "Brand"}, inplace=True, errors="ignore")
    df["Brand"] = df["Brand"].astype(str).str.title().str.strip()
    df["COUNTY_KEY"] = df["County"]
    for col in [
        "White Space Score",
        "Client Market Share",
        "Competitor Strength",
        "ERP GT Sales Coverage",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df
