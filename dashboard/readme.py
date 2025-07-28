import streamlit as st

def page_readme():
    st.title("📖 Pwani Kenya Dashboard – User Guide")

    st.markdown(
        """
## What’s Inside?

This dashboard is a five-page suite that moves from **high-level market health** to **granular SKU pricing** and ends with **downloadable brand reports**.  
All pages share the same dark theme and respond instantly to filters.

| Page | Name | 30-sec Purpose |
|------|------|----------------|
| **1** | **Main Dashboard – SUMMARY** | National snapshot of key KPIs.<br>Filter by **Brand** or **Territory** to update KPIs, interactive map and two sales / share charts. |
| **2** | **Territory Deep-Dive** | Drill into a single territory: hot-zone map, KPI strip, competitor vs. client bar, AWS histogram to understand AWS distribution in territory. |
| **3** | **SKU-Level Analysis** | Cluster performance, *quarterly* pricing impact, PED bubbles and market-share change. |
| **4** | **Distribution Opportunities** | Geo heat-map of distributor reach + opportunity matrix to rank under-penetrated regions. |
| **5** | **Export & Report** | Brand-level report builder with executive summary, KPI cards, high-potential list and one-click PDF/CSV/XLSX export. |

---

## Key Metrics / Parameters

| Metric | Where Used | Quick Definition |
|--------|-----------|------------------|
| **White Space Score** | Pages 1-2 | Market potential not yet captured (0-100). |
| **Client Share** | Pages 1-2 | `(Brand Sales / Total Market Sales) × 100` |
| **Competitor Strength** | Pages 1-2 | Aggregate share of all competitors in scope. |
| **AWS** (RTM) | Pages 1-2 | RTM “hot-zone” opportunity score (0-50+). |
| **PED** | Pages 3 | Price Elasticity of Demand (∆Qty / ∆Price). |
| **Opportunity Score** | Page 4 | `0.6×White Space + 0.1×RTM – 0.3×GT Coverage + 100` |


---

## Quick Navigation Tips

* **Filters drive everything** – each page’s dropdowns update maps, charts and KPI cards in real-time.  
* Hover on choropleth maps and bars to see tooltips with exact numbers.  
* Use the **Export & Report** page to download PDF or CSV packs branded per territory.

---

### Data Sources

* **GT Channel**: sales, market share, SKU clusters.  
* **RTM Monthly**: average base price, volume, PED, hot-zone coordinates.  
* **GeoJSON**: Kenya county + territory shapes.  
* **Distributor Lat-Longs**: RTM coverage (20 km urban / 30 km rural).  

> All data tables are cached in memory for snappy page switches 🔄.

---

### Version Notes

* **v1.0** (2025-05-20) – initial 6-page release  
"""
    )