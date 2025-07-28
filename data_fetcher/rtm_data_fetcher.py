import pandas as pd
from utils import ensure_str_col
from constants import dc



def load_rtm_main():

    rtm = pd.read_csv(dc.RTM_FILE_SUBCOUNTY)
    rtm.columns = rtm.columns.str.strip().str.title()
    rtm[["Territory", "County", "Subcounty", "Brand"]] = rtm[
        ["Territory", "County", "Subcounty", "Brand"]
    ].apply(lambda s: s.str.title().str.strip())

    comp_df = pd.read_excel(dc.COMP_FILE)
    comp_df.columns = comp_df.columns.str.strip()
    comp_df.rename(columns={"Market": "Territory"}, inplace=True)
    comp_df["Territory"] = comp_df["Territory"].str.title().str.strip()
    comp_df["BRAND"] = comp_df["BRAND"].str.title().str.strip()
    comp_df["Competitor"] = comp_df["Competitor"].str.title().str.strip()

    return rtm, comp_df

def load_rtm():
    rtm = pd.read_csv(dc.RTM_FILE_MONTH)
    ensure_str_col(rtm, "MARKET", "REGION_NAME", "Markets")
    ensure_str_col(rtm, "BRAND", "Brand")
    ensure_str_col(rtm, "SKU", "SKU")
    if "Volume" in rtm.columns and "VOLUME" not in rtm.columns:
        rtm = rtm.rename(columns={"Volume": "VOLUME"})
    return rtm

