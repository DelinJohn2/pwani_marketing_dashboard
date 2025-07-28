import re
import pandas as pd
import pathlib
from constants import dc


gt_data = pd.read_excel(dc.GT_FILE)
percentage_data = pd.read_excel(
    dc.PERCENTAGE_FILE
)
top_location_data = pd.read_csv(dc.TOP_LOCATION_FILE)

# --- helper functions (unchanged) ------------------------------------
def executive_summary_retirver(text):
    m = re.search(r"## 1. Executive Summary\s*(.*?)(?=\n##|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_territory_block(text, territory_name):
    m = re.search(
        rf"### {territory_name}\n(.*?)(?=\n### [A-Z ]+|\Z)", text, re.DOTALL
    )
    return m.group(0).strip() if m else None

def extract_data(txt):
    ws = re.search(r"\*\*White Space Score\*\*:\s*([\d.]+)", txt)
    cs = re.search(r"\*\*Client Share\*\*:\s*([\d.]+)%", txt)
    ins = re.findall(r"### Insights\s*(.*?)(?=\n###|\n##|\Z)", txt, re.DOTALL)
    return {
        "white_space_scores": ws.group(1) + " %" if ws else None,
        "client_shares": cs.group(1) + " %" if cs else None,
        "insights": [" ".join(i.strip().split()) for i in ins],
    }

def get_top_location(territory, brand):
    rows = top_location_data[
        (top_location_data["Territory"] == territory)
        & (top_location_data["Brand"] == brand)
    ]
    return ",".join(rows["Top 3 Performing Location"].values)

def text_extractor(territories, brand):
    data_dict = {
        "Territory": [],
        "White Space Scores": [],
        "Client Shares": [],
        "Summary": [],
        "High Potential Regions": [],
    }
    try:
        md_path = pathlib.Path(f"md_files/{brand}.md")
        content = md_path.read_text(encoding="utf-8")
        exec_sum = executive_summary_retirver(content)
        for terr in territories:
            block = extract_territory_block(content, terr)
            if not block:
                continue
            d = extract_data(block)
            top_loc = get_top_location(terr, brand)
            data_dict["Territory"].append(terr)
            data_dict["White Space Scores"].append(d["white_space_scores"])
            data_dict["Client Shares"].append(d["client_shares"])
            data_dict["Summary"].append(" ".join(d["insights"]))
            data_dict["High Potential Regions"].append(top_loc)
        return data_dict, exec_sum
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Markdown file for brand '{brand}' not found in 'md_files' directory."
        )
        

def Population_percentage_per_brand(brand, territory):
    try:

        data = percentage_data[percentage_data["Territory"] == territory]

        if data.empty:
            return None, None, None  # or raise an error

        total_population = data["Total Population"].sum()

        # Assuming only one row should match per territory
        brand_percentage = data[brand].iloc[0]  # get the scalar value
        brand_population = (brand_percentage / 100) * total_population

        brand_percentage = f"Target Audience Fit: {brand_percentage:.2f}%"
        brand_population = f"Target Audience Population: {brand_population:,.0f}"
        total_population = (
            f"Total Population of {territory}: {total_population:,.0f}"
        )

        return total_population, brand_percentage, brand_population
    except KeyError:
        raise KeyError(f"Column '{brand}' not found in the percentage data.")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def average_ws(brand):
    return round(gt_data[gt_data["brand"] == brand]["White Space Score"].mean(), 2)