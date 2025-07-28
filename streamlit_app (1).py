# ─────────────────────────────────────────────────────────────────────────────
#  PAGE 1 – Main Dashboard
#  GT Territory view  ➜  MT County view + Cluster-Bubble map
#  Author : Harshit   •  Latest UI refactor : 2025-05-31
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#  Main Dashboard  –  GT Territory view / MT County view
#  * Zero-score areas show white colour and custom hover
#  * All Plotly charts/maps have a black border
# ─────────────────────────────────────────────────────────────────────────────
CLUSTER_FILEGEO_FILE
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, geopandas as gpd
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json, re
from pathlib import Path
import importlib.util
from sklearn.cluster import KMeans

with open("styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ╭──────────────────────────  APP CONFIG  ──────────────────────────╮
st.set_page_config(
    page_title="Pwani Dashboards · Main",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊",
)

NAVY_BG, PANEL_BG, FG_TEXT = "#0F1C2E", "#e3e8ef", "#e3e8ef"

# st.markdown(f"""
# <style>
# html,body,[data-testid=stApp]{{background:{NAVY_BG};color:{FG_TEXT};
#                                font-family:'Segoe UI',sans-serif}}
# h1,h2,h3,h4,h5,h6{{color:#fff;margin:0}}
# .stDataFrame div[data-testid=stVerticalBlock]{{background:{PANEL_BG}}}
# /* black outline for every Plotly object */
# .stPlotlyChart{{border:1px solid #000;border-radius:4px;padding:2px}}
# .stPlotlyChart>div{{background:{NAVY_BG}!important}}
# </style>""", unsafe_allow_html=True)

# ╭──────────────────────────  FILE PATHS  ──────────────────────────╮
GT_FILE = "GT_DATA_122_merged_filled.xlsx"
TERR_GJ = "kenya_territories (1).geojson"
RTM_FILE = "RTM_SUBCOUNTY_ANALYSIS_updated_approch (2).csv"
COUNTY_GJ = "kenya.geojson"
MT_FILE = "MT_WHITE_SPACE_SCORE_CLEANED.xlsx"
CLUSTER_FILE = "MT_CLUSTER_2_With_County.xlsx"
COMP_FILE = "PWANI_COMP_STD_final_confirmed.xlsx"


def load_rtm_main():

    rtm = pd.read_csv(RTM_FILE)
    rtm.columns = rtm.columns.str.strip().str.title()
    rtm[["Territory", "County", "Subcounty", "Brand"]] = rtm[
        ["Territory", "County", "Subcounty", "Brand"]
    ].apply(lambda s: s.str.title().str.strip())

    comp_df = pd.read_excel(COMP_FILE)
    comp_df.columns = comp_df.columns.str.strip()
    comp_df.rename(columns={"Market": "Territory"}, inplace=True)
    comp_df["Territory"] = comp_df["Territory"].str.title().str.strip()
    comp_df["BRAND"] = comp_df["BRAND"].str.title().str.strip()
    comp_df["Competitor"] = comp_df["Competitor"].str.title().str.strip()

    return rtm, comp_df


RTM_DF, COMP_DF = load_rtm_main()

SALES = "ERP GT Sales Coverage"
CS = "Client Market Share"
COMP = "Competitor Strength"
WS = "White Space Score"
AWS = "Aws"



# ╭──────────────────────  DATA LOADERS (cached)  ───────────────────╮
@st.cache_data(show_spinner="Loading GT & territory …")
def load_gt_terr():
    gt = (
        pd.read_excel(GT_FILE)
        .rename(columns=str.strip)
        .rename(columns={"brand": "Brand", "Markets": "Territory"})
    )
    gt["Territory"] = gt["Territory"].str.title().str.strip()
    gt["Brand"] = gt["Brand"].str.title().str.strip()
    gt["TERR_KEY"] = gt["Territory"]

    terr = json.loads(Path(TERR_GJ).read_text("utf-8"))
    for f in terr["features"]:
        f["properties"]["TERR_KEY"] = f["properties"]["TERRITORY"].title().strip()
    return gt, terr


@st.cache_data(show_spinner="Loading MT KPIs …")
def load_mt():
    df = pd.read_excel(MT_FILE)
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


@st.cache_data(show_spinner="Loading county GeoJSON …")
def load_county_geo():
    geo = json.loads(Path(COUNTY_GJ).read_text("utf-8"))
    for f in geo["features"]:
        nm = f["properties"].get("COUNTY_NAM") or f["properties"].get("NAME", "")
        f["properties"]["COUNTY_KEY"] = nm.title().strip()
    return geo


@st.cache_data(show_spinner="Loading cluster bubbles …")
def load_bubbles():
    df = pd.read_excel(CLUSTER_FILE)
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


def county_centroids(geojson):
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    gdf = gdf.to_crs(3857)
    gdf["geometry"] = gdf.geometry.centroid
    gdf = gdf.to_crs(4326)
    gdf["lon"], gdf["lat"] = gdf.geometry.x, gdf.geometry.y
    return gdf[["COUNTY_KEY", "lon", "lat"]]
NAVY_BG

GT_DF, TERR_GEO = load_gt_terr()
MT_DF = load_mt()
COUNTY_GEO = load_county_geo()
MT_CLUSTER_DF = load_bubbles()
COUNTY_CENTROIDS = county_centroids(COUNTY_GEO)

# ╭──────────────────────────  HELPERS  ─────────────────────────────╮
percent = lambda s: (s * 100 if s.max() <= 1 else s).round(2)
AXIS = dict(color="#9FB4CC", gridcolor="#24364F")
COLOR_CLUSTERS = {
    "Green": "#2ECC71",
    "Blue": "#3498DB",
    "Yellow": "#F1C40F",
    "White": "#ECF0F1",
    "Purple": "#9B59B6",
    "Red": "#E74C3C",
}


def spacer(px=25):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


def add_zero_layer(fig, geojson, key_field, zero_keys, hovertxt):
    """Paint polygons pure white for territories/counties with score 0."""
    if not zero_keys:
        return
    z_polys = [
        f for f in geojson["features"] if f["properties"][key_field] in zero_keys
    ]
    fig.add_trace(
        go.Choroplethmapbox(
            geojson={"type": "FeatureCollection", "features": z_polys},
            locations=[p["properties"][key_field] for p in z_polys],
            featureidkey=f"properties.{key_field}",
            # any constant z; colourscale forces white
            z=[0] * len(z_polys),
            colorscale=[[0, "white"], [1, "white"]],
            autocolorscale=False,
            showscale=False,
            marker_line_color="rgba(0,0,0,0.35)",
            marker_line_width=0.4,
            name="Not present here",
            hovertemplate=f"{hovertxt}<extra></extra>",
        )
    )


def draw_bubble_map(df):
    grid = (
        df.groupby(["County", "Cluster"], as_index=False)["Volume"]
        .sum()
        .merge(COUNTY_CENTROIDS, left_on="County", right_on="COUNTY_KEY", how="left")
    )
    outline = go.Choroplethmapbox(
        geojson=COUNTY_GEO,
        locations=[f["properties"]["COUNTY_KEY"] for f in COUNTY_GEO["features"]],
        z=[0] * len(COUNTY_GEO["features"]),
        showscale=False,
        marker=dict(line=dict(color="rgba(180,180,180,0.25)", width=0.4)),
    )
    px_fig = px.scatter_mapbox(
        grid,
        lat="lat",
        lon="lon",
        size="Volume",
        size_max=45,
        color="Cluster",
        color_discrete_map=COLOR_CLUSTERS,
        hover_data=dict(County=True, Cluster=True, Volume=True, lat=False, lon=False),
    )
    fig = go.Figure([outline] + list(px_fig.data))
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            zoom=5.5,
            center=dict(lat=0.23, lon=37.9),
            layers=[
                dict(
                    sourcetype="geojson",
                    type="fill",
                    below="traces",
                    source={
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [10, -35],
                                            [70, -35],
                                            [70, 25],
                                            [10, 25],
                                            [10, -35],
                                        ]
                                    ],
                                },
                            }
                        ],
                    },
                    color="rgba(0,120,255,0.15)",
                )
            ],
        ),
        height=520,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor=NAVY_BG,
        plot_bgcolor=NAVY_BG,
        font_color=FG_TEXT,
    )
    return fig


# ╭────────────────────────  PAGE FUNCTION  ─────────────────────────╮
def page_main_dashboard():
    # st.markdown("## Main Dashboard")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        mode = st.selectbox("Data Source", ("GT – Territory View", "MT – County View"))
    is_mt = mode.startswith("MT")
    df, geo, region, key = (
        (GT_DF, TERR_GEO, "Territory", "TERR_KEY")
        if not is_mt
        else (MT_DF, COUNTY_GEO, "County", "COUNTY_KEY")
    )
    with c2:
        brand = st.selectbox("Brand", ["All"] + sorted(df["Brand"].unique()))
    with c3:
        sel = st.selectbox(region, ["All"] + sorted(df[region].unique()))
        view = df.copy()
        if brand != "All":
            view = view[view["Brand"] == brand]
        if sel != "All":
            view = view[view[region] == sel]

    # KPI strip
    k1, k2, k3 = st.columns(3)
    for box, title, val in zip(
        [k1, k2, k3],
        ["White Space Score", "Client Market Share", "Competitor Strength"],
        [
            f"{view['White Space Score'].mean():.0f}",
            f"{percent(view['Client Market Share']).mean():.1f}%",
            f"{percent(view['Competitor Strength']).mean():.1f}%",
        ],
    ):
        box.markdown(
            f"""
            <div class="kpiCardStyle">
                <h5>{title}</h5>
                <p>{val}</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    spacer()

    # ────────────────────────────────────────────────────────────────
    #  GT  = single row    ·    MT  = two rows
    # ────────────────────────────────────────────────────────────────
    if not is_mt:
        map_col, _, bar_col = st.columns([1.5, 0.01, 1])

        with map_col:
            base = df if brand == "All" else df[df["Brand"] == brand]
            full_keys = [f["properties"][key] for f in geo["features"]]
            mdf = (
                pd.DataFrame({key: full_keys})
                .merge(
                    base.groupby(key, as_index=False)["White Space Score"].mean(),
                    how="left",
                )
                .fillna({"White Space Score": 0})
            )
            if sel != "All":
                mdf.loc[mdf[key] != sel, "White Space Score"] = 0

            # Discrete bins
            bins = [0, 10, 20, 30, 40, 50, 60, np.inf]
            labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60+"]
            mdf["ws_bin"] = pd.cut(
                mdf["White Space Score"],
                bins=bins,
                labels=labels,
                right=False,
                include_lowest=True,
            )
            BIN_COLOURS = {
                "0-10": "#ffffcc",  # very light yellow
                "10-20": "#ffeda0",  # light yellow-orange
                "20-30": "#fed976",  # yellow-orange
                "30-40": "#feb24c",  # orange
                "40-50": "#fd8d3c",  # strong orange-red
                "50-60": "#f03b20",  # red-orange
                "60+": "#bd0026",  # deep red
            }

            fig = px.choropleth_mapbox(
                mdf,
                geojson=geo,
                locations=key,
                featureidkey=f"properties.{key}",
                color="ws_bin",
                category_orders={"ws_bin": labels},
                color_discrete_map=BIN_COLOURS,
                mapbox_style="carto-positron",
                center=dict(lat=0.23, lon=37.9),
                zoom=5,
                opacity=0.9,
                height=520,
                width=1050,
                hover_data={"ws_bin": True, "White Space Score": ":.1f"},
            )
            # blue overlay
            # fig.add_shape(
            #     type="rect",
            #     xref="paper",
            #     yref="paper",
            #     x0=0,
            #     x1=1.05,
            #     y0=0,
            #     y1=1.05,
            #     line=dict(color="#0278b7", width=2),
            #     layer="above",
            # )
            fig.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                mapbox=dict(
                    layers=[
                        dict(
                            sourcetype="geojson",
                            type="fill",
                            below="traces",
                            source={
                                "type": "FeatureCollection",
                                "features": [
                                    {
                                        "type": "Feature",
                                        "geometry": {
                                            "type": "Polygon",
                                            "coordinates": [
                                                [
                                                    [10, -35],
                                                    [70, -35],
                                                    [70, 25],
                                                    [10, 25],
                                                    [10, -35],
                                                ]
                                            ],
                                        },
                                    }
                                ],
                            },
                            color="rgba(0,120,255,0)",
                        )
                    ]
                ),
                paper_bgcolor="#fff",
                plot_bgcolor="#fff",
                font_color=FG_TEXT,
            )

            add_zero_layer(
                fig,
                geo,
                key,
                mdf.loc[mdf["White Space Score"] == 0, key].tolist(),
                "You are not selling here",
            )
            st.plotly_chart(fig, use_container_width=False)
        with bar_col:
            comp = (
                (df if brand == "All" else df[df["Brand"] == brand])
                .groupby(region, as_index=False)[
                    ["Client Market Share", "Competitor Strength"]
                ]
                .mean()
            )
            comp["Client Market Share"] = percent(comp["Client Market Share"])
            comp["Competitor Strength"] = percent(comp["Competitor Strength"])
            op = [1 if (sel == "All" or r == sel) else 0.3 for r in comp[region]]

            stk = go.Figure()
            stk.add_bar(
                name="Client Share",
                x=comp[region],
                y=comp["Client Market Share"],
                marker_color="#00B4D8",
                marker_opacity=op,
            )
            stk.add_bar(
                name="Competitor Strength",
                x=comp[region],
                y=comp["Competitor Strength"],
                marker_color="#0077B6",
                marker_opacity=op,
            )
            stk.update_layout(
                barmode="stack",
                height=250,
                title="Market Composition",
                paper_bgcolor="#e3e8ef",
                plot_bgcolor="#e3e8ef",
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=AXIS,
                yaxis=AXIS,
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.25, bgcolor="rgba(0,0,0,0)"
                ),
            )
            st.plotly_chart(stk, use_container_width=True)

            sales = (
                (df if brand == "All" else df[df["Brand"] == brand])
                .groupby(region, as_index=False)["ERP GT Sales Coverage"]
                .sum()
            )
            sop = [1 if (sel == "All" or r == sel) else 0.3 for r in sales[region]]
            erp = go.Figure(
                go.Bar(
                    x=sales[region],
                    y=sales["ERP GT Sales Coverage"],
                    marker_color="#48CAE4",
                    marker_opacity=sop,
                )
            )
            erp.update_layout(
                title="Sales",
                height=252,
                paper_bgcolor="#e3e8ef",
                plot_bgcolor="#e3e8ef",
                bargap=0.15,
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis=AXIS,
                yaxis=AXIS,
                showlegend=False,
            )
            st.plotly_chart(erp, use_container_width=True)

        spacer()
        st.markdown("---")
        st.markdown("### Detailed Dataset")
        st.dataframe(df, height=350, use_container_width=True)
        spacer(20)

    else:  # ---------- MT VIEW ----------------------------
        map_l, map_r = st.columns(2)

        with map_l:
            st.markdown("### MT White Space")
            base = df if brand == "All" else df[df["Brand"] == brand]
            all_counties = [
                f["properties"]["COUNTY_KEY"] for f in COUNTY_GEO["features"]
            ]
            mdf = (
                pd.DataFrame({"COUNTY_KEY": all_counties})
                .merge(
                    base.groupby("COUNTY_KEY", as_index=False)[
                        "White Space Score"
                    ].mean(),
                    how="left",
                )
                .fillna({"White Space Score": 0})
            )
            if sel != "All":
                mdf.loc[mdf["COUNTY_KEY"] != sel, "White Space Score"] = 0
            fig_c = px.choropleth_mapbox(
                mdf,
                geojson=COUNTY_GEO,
                locations="COUNTY_KEY",
                featureidkey="properties.COUNTY_KEY",
                color="White Space Score",
                color_continuous_scale="YlOrRd",
                range_color=(0, 60),
                mapbox_style="carto-positron",
                center=dict(lat=0.23, lon=37.9),
                zoom=5,
                opacity=0.9,
                height=520,
            )
            fig_c.update_layout(
                mapbox=dict(
                    layers=[
                        dict(
                            sourcetype="geojson",
                            type="fill",
                            below="traces",
                            source={
                                "type": "FeatureCollection",
                                "features": [
                                    {
                                        "type": "Feature",
                                        "geometry": {
                                            "type": "Polygon",
                                            "coordinates": [
                                                [
                                                    [10, -35],
                                                    [70, -35],
                                                    [70, 25],
                                                    [10, 25],
                                                    [10, -35],
                                                ]
                                            ],
                                        },
                                    }
                                ],
                            },
                            color="rgba(0,120,255,0.15)",
                        )
                    ]
                ),
                # paper_bgcolor=NAVY_BG,plot_bgcolor=NAVY_BG,
                margin=dict(l=0, r=0, t=30, b=0),
                font_color=FG_TEXT,
            )
            add_zero_layer(
                fig_c,
                COUNTY_GEO,
                "COUNTY_KEY",
                mdf.loc[mdf["White Space Score"] == 0, "COUNTY_KEY"].tolist(),
                "Not present here",
            )
            fig_c.update_layout(legend=dict(traceorder="normal"))
            st.plotly_chart(fig_c, use_container_width=True)

        with map_r:
            st.markdown("### Cluster Density by County")
            bub = MT_CLUSTER_DF.copy()
            if brand != "All":
                bub = bub[bub["Brand"] == brand]
            if sel != "All":
                bub = bub[bub["County"] == sel]
            st.plotly_chart(draw_bubble_map(bub), use_container_width=True)

        spacer()

        gcol, tcol = st.columns(2)

        with gcol:
            st.markdown("### Market and Sales")

            comp = df.groupby("County", as_index=False)[
                ["Client Market Share", "Competitor Strength"]
            ].mean()
            comp["Client Market Share"] = percent(comp["Client Market Share"])
            comp["Competitor Strength"] = percent(comp["Competitor Strength"])
            op = [1 if (sel == "All" or r == sel) else 0.3 for r in comp["County"]]

            stack = go.Figure()
            stack.add_bar(
                name="Client Share",
                x=comp["County"],
                y=comp["Client Market Share"],
                marker_color="#00B4D8",
                marker_opacity=op,
            )
            stack.add_bar(
                name="Competitor Strength",
                x=comp["County"],
                y=comp["Competitor Strength"],
                marker_color="#0077B6",
                marker_opacity=op,
            )
            stack.update_layout(
                barmode="stack",
                height=260,
                title="Market Composition",
                paper_bgcolor=PANEL_BG,
                plot_bgcolor=PANEL_BG,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=AXIS | dict(tickangle=-45),
                yaxis=AXIS,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"
                ),
            )
            st.plotly_chart(stack, use_container_width=True)

            sales = df.groupby("County", as_index=False)["ERP GT Sales Coverage"].sum()
            sop = [1 if (sel == "All" or r == sel) else 0.3 for r in sales["County"]]
            erp = go.Figure(
                go.Bar(
                    x=sales["County"],
                    y=sales["ERP GT Sales Coverage"],
                    marker_color="#48CAE4",
                    marker_opacity=sop,
                )
            )
            erp.update_layout(
                title="Sales",
                height=260,
                paper_bgcolor=PANEL_BG,
                plot_bgcolor=PANEL_BG,
                bargap=0.15,
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis=AXIS | dict(tickangle=-45),
                yaxis=AXIS,
                showlegend=False,
            )
            st.plotly_chart(erp, use_container_width=True)

        with tcol:
            st.markdown("### Detailed Dataset")
            st.dataframe(df, height=520, use_container_width=True)
            st.caption(
                "Sources – GT KPI & Territory GeoJSON • MT KPI & Cluster Bubbles • Kenya County GeoJSON"
            )

        spacer(20)


# ────────────────────────────────────────────────────────────────────
#  NAVIGATION update  ➜ remove “MT Dashboard” entry
# ────────────────────────────────────────────────────────────────────


# ╭───────────────────────────────  PAGE 2  ─────────────────────────╮
# Territory Deep-Dive  (unchanged logic, wrapped into a function)
# -------------------------------------------------------------------
# ─────────────────────────────────────────────────────────────────────────────
#  PAGE 2 – Territory Deep Dive
#  Shows the whole of Kenya; if a single territory is picked it’s highlighted,
#  everything else is “blur-grey”.  Selecting **All** colours every polygon.
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#  PAGE 2 – Territory Deep-Dive
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#  PAGE 2 – Territory Deep-Dive  (no blur/highlight, “All” option added)
# ─────────────────────────────────────────────────────────────────────────────
def page_territory_deep_dive():
    """
    Detailed RTM drill-down.
    • Territory filter now includes “All”.
    • Map has no grey-blur or highlight layers – just coloured polygons
      wherever data exists.
    • Charts fill the Streamlit column via use_container_width=True.
    """

    import json, re, html
    from pathlib import Path
    import plotly.express as px
    import plotly.graph_objects as go

    # ───── CONSTANTS --------------------------------------------------------
    TEXT_CSV = "all_brands_competitive_analysis_20250530_140609.csv"
    SUBCOUNTY_GJ = "kenya-subcounties-simplified.geojson"

    # ───── 1 ▸ competitor narrative CSV (cached) ---------------------------
    @st.cache_data(show_spinner="Loading competitor narrative …")
    def _load_comp_text():
        df = pd.read_csv(TEXT_CSV)
        df.columns = df.columns.str.strip()
        df[["Brand", "Competitor", "Territory"]] = df[
            ["Brand", "Competitor", "Territory"]
        ].apply(lambda s: s.astype(str).str.title().str.strip())
        return df

    COMP_TXT_DF = _load_comp_text()

    # ───── 2 ▸ sub-county GeoJSON (cached) ---------------------------------
    @st.cache_data(show_spinner="Loading sub-county shapes …")
    def _load_sub_geo():
        geo = json.loads(Path(SUBCOUNTY_GJ).read_text("utf-8"))
        for f in geo["features"]:
            name = (
                (
                    f["properties"].get("shapeName")
                    or f["properties"].get("SubCounty")
                    or f["properties"].get("Subcounty")
                    or f["properties"].get("SUB_COUNTY")
                    or f["properties"].get("NAME", "")
                )
                .title()
                .strip()
            )
            f["properties"]["SUB_KEY"] = name
        return geo

    SUBCOUNTY_GEO = _load_sub_geo()

    # ───── 3 ▸ HEADER & FILTER WIDGETS -------------------------------------
    st.markdown("## Territory Deep-Dive")

    c1, c2, c3 = st.columns([1, 1, 1])
    territory = c1.selectbox("Territory", ["All"] + sorted(GT_DF["Territory"].unique()))
    brand_list = ["All"] + sorted(GT_DF["Brand"].unique())
    default_brand_idx = (
        brand_list.index("Ushindi Bar") if "Ushindi Bar" in brand_list else 0
    )
    brand = c2.selectbox("Brand", brand_list, index=default_brand_idx)
    level_options = ["County", "Sub-County"]
    level = c3.selectbox(
        "Map granularity", level_options, index=level_options.index("Sub-County")
    )  # default to Sub-County)

    # ───── 4 ▸ KPI CARDS ----------------------------------------------------
    view_df = GT_DF.copy()
    if territory != "All":
        view_df = view_df[view_df["Territory"] == territory]
    if brand != "All":
        view_df = view_df[view_df["Brand"] == brand]

    k1, k2, k3, k4 = st.columns(4)
    for box, title, value in zip(
        [k1, k2, k3, k4],
        ["Total Sales", "Market Share", "Competitor Strength", "White Space"],
        [
            f"{view_df[SALES].sum():,.0f}",
            f"{percent(view_df[CS]).mean():.1f}%",
            f"{percent(view_df[COMP]).mean():.1f}%",
            f"{view_df[WS].mean():.0f}",
        ],
    ):
        box.markdown(
            f"""<div class="kpiCardStyle"><h5>{title}</h5><p>{value}</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")  # spacer line

    # ───── 5 ▸ FILTER RTM ROWS --------------------------------------------
    rtm = RTM_DF.copy()
    if territory != "All":
        rtm = rtm[rtm["Territory"] == territory]
    if brand != "All":
        rtm = rtm[rtm["Brand"] == brand]

    # If no data, stop early with a message
    if rtm.empty:
        st.warning("No RTM rows for the current filter – nothing to plot.")
        return

    # ───── 6 ▸ BUILD MAP ----------------------------------------------------
    left, right = st.columns(2)

    with left:
        st.markdown("### RTM Hot-Zones")

        if level == "County":
            geo_src, id_field, key_col = COUNTY_GEO, "COUNTY_KEY", "County"
        else:
            # detect sub-county column automatically
            def _match(c):
                return "sub" in c.lower() and "county" in c.lower()

            key_col = next((c for c in rtm.columns if _match(c)), None)
            if key_col is None:
                st.error("❌ Sub-county column not found in RTM data.")
                st.stop()
            geo_src, id_field = SUBCOUNTY_GEO, "SUB_KEY"

        # full list of polygons to colour (Kenya map)
        all_keys = [f["properties"][id_field] for f in geo_src["features"]]

        # Add AWS_Bin column (if not already done)
        aws_bins = [0, 20, 40, 60, 80, 100]
        aws_labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]
        rtm["AWS_Bin"] = pd.cut(
            rtm[AWS], bins=aws_bins, labels=aws_labels, include_lowest=True, right=False
        )

        # Get selected AWS bin from session_state
        selected_range = st.session_state.get("aws_range", "All")

        # Merge AWS value into map
        map_df = pd.DataFrame({id_field: all_keys}).merge(
            rtm[[key_col, AWS, "AWS_Bin"]].rename(columns={key_col: id_field}),
            how="left",
        )

        # Filter map data based on selected bin
        if selected_range != "All":
            map_df["visible"] = map_df["AWS_Bin"] == selected_range
            map_df.loc[~map_df["visible"], AWS] = 0  # or np.nan for total hide
        else:
            map_df["visible"] = True

        map_df = map_df.fillna({AWS: 0})

        mfig = px.choropleth_mapbox(
            map_df,
            geojson=geo_src,
            locations=id_field,
            featureidkey=f"properties.{id_field}",
            color=AWS,
            color_continuous_scale="YlOrRd",
            range_color=(0, 100),
            mapbox_style="carto-positron",
            center={"lat": 0.23, "lon": 37.9},
            zoom=5,
            opacity=0.9,
            height=520,
        )

        mfig.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(mfig, use_container_width=True)

    # ───── 7 ▸ AWS HISTOGRAM ----------------------------------------------
    from streamlit_plotly_events import plotly_events

    with right:
        st.markdown("### AWS Score Distribution")

        aws_bins = [0, 20, 40, 60, 80, 100]
        aws_labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]

        rtm = rtm.copy()
        rtm[AWS] = pd.to_numeric(rtm[AWS], errors="coerce")
        rtm["AWS_Bin"] = pd.cut(
            rtm[AWS], bins=aws_bins, labels=aws_labels, include_lowest=True, right=False
        )

        # ───── Clear Button FIRST ─────
        # Create two columns: one for the button and one for the selected range
        col_clear, col_label = st.columns([2, 4])

        with col_clear:
            if st.button("Clear AWS Filter"):
                selected_range = st.session_state.get("aws_range", "All")
                if selected_range != "All":
                    st.session_state["aws_range"] = "All"
                    st.rerun()

        with col_label:
            st.markdown(f"**Selected Range:** `{selected_range}`")


        # ───── Histogram ─────
        hist = px.histogram(
            rtm,
            x="AWS_Bin",
            color_discrete_sequence=["#38bdf8"],
            labels={"AWS_Bin": "AWS Score Bin"},
            category_orders={"AWS_Bin": aws_labels},
        )

        hist.update_layout(
            height=460,
            bargap=0.25,
            paper_bgcolor="#e3e8ef",
            plot_bgcolor="#e3e8ef",
            xaxis=dict(title="AWS Score", tickmode="array", tickvals=aws_labels),
            yaxis=AXIS,
            margin=dict(l=0, r=0, t=30, b=30),
            clickmode="event+select",
        )
        hist.update_layout(
            shapes=[  # Add border to the plot area
                {
                    "type": "rect",
                    "type": "rect",
                    "x0": 0,
                    "y0": -0.075,  # Adjusted for top margin (0.05 from the top)
                    "x1": 1,
                    "y1": 1.075,
                    "xref": "paper",
                    "yref": "paper",
                    "line": {
                        "color": "#0077b6",  # Border color
                        "width": 1,  # Border width
                    },
                }
            ]
        )

        # ───── Interactivity ─────
        selected_points = plotly_events(
            hist, click_event=True, select_event=True, override_height=520
        )

        if selected_points:
            new_range = selected_points[0]["x"]
            if selected_range != new_range:
                st.session_state["aws_range"] = new_range
                st.rerun()

        # st.plotly_chart(hist, use_container_width=True)


# ╭───────────────────────────────  PAGE 3  ─────────────────────────╮

# ───────────────────────── imports
# Page 3 – SKU-Cluster Dashboard (SKU filter only affects price buckets)
# Page 3 – SKU Cluster Dashboard
# Brand-aware SKU filter (affects price bucket panel only)

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objs as go
import json
from pathlib import Path
from sklearn.cluster import KMeans

# ───────── paths
GT_FILE = Path("GT_DATA_122_merged_filled.xlsx")
RTM_FILE = Path("RTM_MONTH DATA.csv")
GEO_FILE = Path("kenya_territories (1).geojson")

# ───────── theme + colour helpers
PANEL_BG = "#0e1b2c"
BASE_COLOURS = {
    "RED": "#E74C3C",
    "YELLOW": "#F1C40F",
    "GREEN": "#2ECC71",
    "BLUE": "#3498DB",
    "WHITE": "#ECF0F1",
    "BLACK": "#34495E",
    "PURPLE": "#9B59B6",
    "ORANGE": "#E67E22",
}


def colour_for(cluster: str) -> str:
    first = str(cluster).split()[0].upper()
    return BASE_COLOURS.get(first, "#95A5A6")


def ensure_str_col(df: pd.DataFrame, name: str, *src):
    """Guarantee df[name] exists as string Series; pull from first src col."""
    for c in src:
        if c in df.columns:
            df[name] = df[c].astype(str)
            break
    if name not in df.columns:
        df[name] = pd.Series([""] * len(df), dtype=str)
    df[name] = df[name].str.upper().str.strip()


# ───────── load GT
@st.cache_data(show_spinner="Loading GT …")
def load_gt():
    df = pd.read_excel(GT_FILE)
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
    return df


# ───────── load RTM
@st.cache_data(show_spinner="Loading RTM …")
def load_rtm():
    rtm = pd.read_csv(RTM_FILE)
    ensure_str_col(rtm, "MARKET", "REGION_NAME", "Markets")
    ensure_str_col(rtm, "BRAND", "Brand")
    ensure_str_col(rtm, "SKU", "SKU")
    if "Volume" in rtm.columns and "VOLUME" not in rtm.columns:
        rtm = rtm.rename(columns={"Volume": "VOLUME"})
    return rtm


# ───────── load map
@st.cache_data(show_spinner="Loading map …")
def load_map():
    poly = gpd.read_file(GEO_FILE).rename(
        columns={"TERRITORY": "MARKET", "REGION_NAME": "MARKET"}
    )
    poly["MARKET"] = poly["MARKET"].str.upper()
    poly = poly.to_crs(3857)
    poly["geometry"] = poly.geometry.centroid
    poly = poly.to_crs(4326)
    poly["lon"] = poly.geometry.x
    poly["lat"] = poly.geometry.y
    cent = poly[["MARKET", "lon", "lat"]].copy()
    return cent, poly


# ───────── bubble map
def draw_cluster_map(df, cent, poly):
    grid = (
        df[["MARKET", "CLUSTER", "SHARE_PCT", "BUBBLE_SIZE", "SHARE_LABEL"]]
        .drop_duplicates()
        .merge(cent, on="MARKET", how="left")
    )
    colour_map = {c: colour_for(c) for c in grid["CLUSTER"].unique()}
    outline = go.Choroplethmapbox(
        geojson=json.loads(poly.to_json()),
        locations=poly["MARKET"],
        z=[0] * len(poly),
        showscale=False,
        marker=dict(line=dict(color="rgba(200,200,200,0.4)", width=0.5)),
    )
    px_fig = px.scatter_mapbox(
        grid,
        lat="lat",
        lon="lon",
        size="BUBBLE_SIZE",
        size_max=50,
        color="CLUSTER",
        color_discrete_map=colour_map,
        hover_data=dict(
            MARKET=True,
            CLUSTER=True,
            SHARE_LABEL=True,
            lat=False,
            lon=False,
            BUBBLE_SIZE=False,
        ),
    )
    fig = go.Figure([outline] + list(px_fig.data))
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=4.5,
        mapbox_center=dict(lat=0.25, lon=37.6),
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
    )
    st.plotly_chart(fig, use_container_width=True)


# ───────── main page
def page_sku_dashboard():
    st.title("SKU-Cluster Dashboard")

    gt = load_gt()
    gt = gt.rename(columns={"ERP GT Sales Coverage": "Sales"})
    rtm = load_rtm()
    cent, poly = load_map()

    # FILTERS
    f = st.columns(5)
    market_sel = f[0].selectbox("Market", ["ALL"] + sorted(gt["MARKET"].unique()))
    brand_sel = f[1].selectbox("Brand", ["ALL"] + sorted(gt["BRAND"].unique()))
    cluster_sel = f[2].selectbox(
        "Cluster", ["ALL"] + sorted(gt["CLUSTER"].dropna().astype(str).unique())
    )
    # SKU list from RTM after market & brand filter
    rtm_pool = rtm.copy()
    if market_sel != "ALL":
        rtm_pool = rtm_pool[rtm_pool["MARKET"] == market_sel]
    if brand_sel != "ALL":
        rtm_pool = rtm_pool[rtm_pool["BRAND"] == brand_sel]
    sku_sel = f[3].selectbox(
        "SKU (price panel only)", ["ALL"] + sorted(rtm_pool["SKU"].dropna().unique())
    )

    period_sel = f[4].selectbox("Period", ["LAST 12 MONTHS"])

    # GT filters (SKU not applied)
    gt_filt = gt.copy()
    if market_sel != "ALL":
        gt_filt = gt_filt[gt_filt["MARKET"] == market_sel]
    if brand_sel != "ALL":
        gt_filt = gt_filt[gt_filt["BRAND"] == brand_sel]
    if cluster_sel != "ALL":
        gt_filt = gt_filt[gt_filt["CLUSTER"] == cluster_sel]
    if gt_filt.empty:
        st.warning("No GT rows for filters.")
        return

    # RTM filters (includes SKU)
    rtm_filt = rtm.copy()
    if market_sel != "ALL":
        rtm_filt = rtm_filt[rtm_filt["MARKET"] == market_sel]
    if brand_sel != "ALL":
        rtm_filt = rtm_filt[rtm_filt["BRAND"] == brand_sel]
    if sku_sel != "ALL":
        rtm_filt = rtm_filt[rtm_filt["SKU"] == sku_sel]

    # Layout panels
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    # 1 Cluster share
    with c1:
        st.subheader("Cluster Share")
        share = gt_filt.groupby("CLUSTER")["Sales"].sum().reset_index()
        share["Percent"] = (share["Sales"] / share["Sales"].sum() * 100).round(1)
        fig = px.bar(
            share,
            x="Percent",
            y="CLUSTER",
            orientation="h",
            text="Percent",
            color="CLUSTER",
            color_discrete_map={c: colour_for(c) for c in share["CLUSTER"]},
        )
        fig.update_traces(texttemplate="%{text:.1f}%")
        fig.update_layout(
            height=260,
            paper_bgcolor=PANEL_BG,
            plot_bgcolor=PANEL_BG,
            showlegend=False,
            margin=dict(l=0, r=0, t=5, b=5),
        )
        st.plotly_chart(fig, use_container_width=True)

    # 2 Price buckets (SKU aware)
    with c2:
        st.subheader("Price Buckets (RTM)")
        if {"AVERAGE_BASE_PRICE", "VOLUME"}.issubset(rtm_filt.columns):
            tmp = rtm_filt.dropna(subset=["AVERAGE_BASE_PRICE", "VOLUME"])
            if tmp["AVERAGE_BASE_PRICE"].nunique() >= 4:
                km = KMeans(n_clusters=4, n_init="auto").fit(
                    tmp[["AVERAGE_BASE_PRICE"]], sample_weight=tmp["VOLUME"]
                )
                tmp["Bucket"] = km.labels_
                centers = km.cluster_centers_.flatten()
                vol = tmp.groupby("Bucket")["VOLUME"].sum()
                bars = pd.DataFrame({"Center": centers, "Volume": vol}).sort_values(
                    "Volume"
                )
                bars["Label"] = "₹" + bars["Center"].round().astype(int).astype(str)
                fig = px.bar(
                    bars,
                    y="Label",
                    x="Volume",
                    orientation="h",
                    color_discrete_sequence=["#F04E4E"],
                )
                fig.update_layout(
                    height=260,
                    paper_bgcolor=PANEL_BG,
                    plot_bgcolor=PANEL_BG,
                    showlegend=False,
                    margin=dict(l=30, r=10, t=30, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough RTM price variation.")
        else:
            st.info("RTM price / volume columns missing.")

    # 3 PED vs sales (SKU ignored)
    with c3:
        st.subheader("PED vs Sales")
        if {"PED", "SALES_VAL"}.issubset(gt_filt.columns):
            ped_df = gt_filt.dropna(subset=["PED", "SALES_VAL"])
            if not ped_df.empty:
                fig = px.scatter(
                    ped_df,
                    x="PED",
                    y="Sales",
                    size="SHARE_PCT",
                    size_max=40,
                    color="CLUSTER",
                    color_discrete_map={
                        c: colour_for(c) for c in ped_df["CLUSTER"].unique()
                    },
                )
                fig.update_layout(
                    height=300,
                    paper_bgcolor=PANEL_BG,
                    plot_bgcolor=PANEL_BG,
                    margin=dict(l=0, r=0, t=5, b=5),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No PED & Sales rows.")
        else:
            st.info("Missing PED or SALES_VAL columns.")

    # 4 Map (SKU ignored)
    with c4:
        st.subheader("Territory Bubble Map")
        draw_cluster_map(gt_filt, cent, poly)


# ╭───────────────────────────────  PAGE 4  ─────────────────────────╮
# Territory–Brand Opportunity Dashboard  (your second standalone app)
# -------------------------------------------------------------------
#  — logic identical, wrapped into function; only set_page_config removed
# -------------------------------------------------------------------
# ╭───────────────────────────────  PAGE 4 NEW  ─────────────────────────╮
# Territory–Brand Opportunity  (replaces the old markdown-driven page)
# -----------------------------------------------------------------------
# ╭───────────────────────────────  PAGE 4  ─────────────────────────╮
# Territory–Brand Opportunity Dashboard (full-width report page)
# -------------------------------------------------------------------
# ─── PAGE 4 · Territory–Brand Opportunity Dashboard ─────────────────────
def page_opportunity_dashboard():
    import re, pandas as pd, streamlit as st, pathlib

    # ── data loads (identical) ───────────────────────────────────────────
    gt_data = pd.read_excel("data_files/GT_DATA_122_merged_filled.xlsx")
    percentage_data = pd.read_excel(
        "data_files/Province Percentage 250410 (1) (1).xlsx"
    )
    top_location_data = pd.read_csv("data_files/Top_3_Brand_Locations.csv")

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
            st.error(f"Markdown for {brand} not found.")
            return {}, ""

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
            st.error(f"Error: Column '{brand}' not found in the percentage data.")
            return None
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None

    def average_ws(brand):
        return round(gt_data[gt_data["brand"] == brand]["White Space Score"].mean(), 2)

    # ── UI layout identical to original ──────────────────────────────────
    st.title("Export and Report Section")

    col1, col2, col3 = st.columns([1.5, 1.5, 3])
    with col1:
        brands = sorted(gt_data["brand"].unique())
        default_index = brands.index("USHINDI BAR") if "USHINDI BAR" in brands else 0
        brand = st.selectbox("Brand", brands, index=default_index)

    territories = ["CENTRAL", "COAST", "LAKE", "NAIROBI", "RIFT VALLEY"]
    table, exec_sum = text_extractor(territories, brand)

    col_a, _ = st.columns([4, 1])
    with col_a:
        st.subheader(f"{brand} - Report")
    st.markdown("---")

    # metric boxes
    col1, col2, col3 = st.columns(3)

    def info_box(title, content):
        st.markdown(
            f"""
            <div style='border:1px solid #ccc;border-radius:10px;
                        padding:1rem;background:#253348;height:180px;overflow-y:auto'>
                <h5 style='margin:0;color:#fff'>{title}</h5>
                <p style='font-size:0.9rem;color:#fff'>{content}</p>
            </div>""",
            unsafe_allow_html=True,
        )

    with col1:
        territory = st.selectbox(
            "Select the Territory", percentage_data["Territory"].unique()
        )
        total_population, brand_population_percentage, brand_population = (
            Population_percentage_per_brand(brand, territory)
        )
        st.write(total_population)
        st.write(brand_population_percentage)
        st.write(brand_population)
    with col2:
        info_box("Average White Space Score", f"{average_ws(brand)} %")
    with col3:
        info_box("Executive Summary", exec_sum.split("\n\n")[0])
    st.markdown("---")

    # table
    st.subheader("Detailed Metric Table")
    df = pd.DataFrame(table)
    st.markdown(
        """
        <style>
        .styled-table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.9rem;
        font-family:'Segoe UI',sans-serif;background:#253348;color:#fff;text-align:center;}
        .styled-table thead tr{background:#253348;color:#fff;}
        .styled-table th,.styled-table td{padding:12px 15px;border:2px solid #fff;text-align:center;}
        .styled-table tbody tr:nth-child(even){background:#354761;}
        </style>
    """,
        unsafe_allow_html=True,
    )
    st.markdown(
        df.to_html(classes="styled-table", index=False, escape=False),
        unsafe_allow_html=True,
    )

    # PDF downloader
    st.markdown("---")
    st.subheader(f"Detailed Report for {brand}")
    report_map = {f"{brand} – {t.title()}": t for t in territories}
    report_map[f"{brand} – For all territories"] = "Complete"
    choice = st.selectbox("Report list", ["Select"] + list(report_map.keys()))
    if choice != "Select":
        loc = report_map[choice]
        path = pathlib.Path(f"Reports/{brand} {loc}.pdf")
        if path.exists():
            st.download_button(
                "Download PDF Report",
                data=path.read_bytes(),
                file_name=path.name,
                mime="application/pdf",
            )
        else:
            st.error(f"⚠️ Report file not found: {path}")


# ╭───────────────────────────────  PAGE 5  ─────────────────────────╮
# Kenya County Opportunity Dashboard  (your third standalone app)
# -------------------------------------------------------------------
MAP_TABLE_HEIGHT = 760
MAP_TABLE_RATIO = [5, 3]


@st.cache_data
def load_counties():
    df = pd.read_csv("Merged_Data_with_Opportunity_Score.csv")
    geo = json.load(open("kenya.geojson", "r", encoding="utf-8"))
    for f in geo["features"]:
        nm = f["properties"].get("COUNTY_NAM") or ""
        f["properties"]["COUNTY_KEY"] = nm.title().strip()
    return df, geo


@st.cache_data
def load_points():
    raw = pd.read_excel("rtm_lat_log.xlsx")
    cols = list(raw.columns)
    lat = next((c for c in cols if re.search(r"^lat", c, re.I)), None)
    lon = next((c for c in cols if re.search(r"(lon|lng)", c, re.I)), None)
    dist = next(
        (c for c in cols if re.search(r"distrib|dealer|partner|outlet", c, re.I)), None
    )
    if None in (lat, lon, dist):
        st.stop()
    pts = raw[[dist, lat, lon]].copy()
    pts.columns = ["Distributor", "Latitude", "Longitude"]
    pts["Latitude"] = pd.to_numeric(pts["Latitude"], errors="coerce")
    pts["Longitude"] = pd.to_numeric(pts["Longitude"], errors="coerce")
    return pts.dropna(subset=["Latitude", "Longitude"])


def page_kenya_dashboard():
    st.markdown("## Kenya County Opportunity Dashboard")

    df, geojson = load_counties()
    pts_df = load_points()

    f1, f2 = st.columns([1, 5])
    with f1:
        brands = ["All"] + sorted(df["BRAND"].dropna().unique())
        choose = st.selectbox("Select Brand", brands)

    view_df = df if choose == "All" else df[df["BRAND"] == choose]

    county_avg = (
        view_df.groupby("County", as_index=False)["Opportunity Score"]
        .mean()
        .assign(County=lambda d: d["County"].str.title().str.strip())
    )

    fig = px.choropleth_mapbox(
        county_avg,
        geojson=geojson,
        locations="County",
        featureidkey="properties.COUNTY_KEY",
        color="Opportunity Score",
        color_continuous_scale="YlOrRd",
        mapbox_style="carto-positron",
        center={"lat": 0.23, "lon": 37.9},
        zoom=5.5,
        opacity=0.9,
        height=MAP_TABLE_HEIGHT,
    )

    fig.add_trace(
        go.Densitymapbox(
            lat=pts_df["Latitude"],
            lon=pts_df["Longitude"],
            z=[1] * len(pts_df),
            radius=14,
            opacity=0.7,
            colorscale=[
                [0, "rgba(0,120,255,0.25)"],
                [0.3, "rgba(0,120,255,0.55)"],
                [1, "rgba(0,120,255,0.9)"],
            ],
            showscale=False,
            name="Distributor Density",
        )
    )

    fig.update_layout(font_color=FG_TEXT, margin=dict(l=0, r=0, t=15, b=0))

    map_col, table_col = st.columns(MAP_TABLE_RATIO)

    with map_col:
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=True))

    with table_col:
        st.markdown("### 📊 Detailed Data Table")
        st.dataframe(
            view_df[
                [
                    "Territory",
                    "County",
                    "BRAND",
                    "subcategory",
                    "Opportunity Score",
                    "AWS",
                ]
            ],
            height=MAP_TABLE_HEIGHT,
            use_container_width=True,
        )


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


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE · MT Dashboard  (county-level clone of “Main Dashboard – SUMMARY”)
#  • Data source  : MT_WHITE_SPACE_SCORE_CLEANED.xlsx  (one row per county × brand)
#  • Map geometry : kenya.geojson   (47 counties, field = COUNTY_NAM)
# ──────────────────────────────────────────────────────────────────────────────
#  Insert this block BELOW the existing imports / constants and ABOVE the
#  PAGE_FUNCS definition in your main Streamlit file.  Nothing else needs to
#  change apart from adding the page to the sidebar list (see bottom).
# ──────────────────────────────────────────────────────────────────────────────

# ———————————————————
# Additional constants
# ———————————————————
MT_FILE = "MT_WHITE_SPACE_SCORE_CLEANED.xlsx"  # cleaned file you produced
COUNTY_GJ = "kenya.geojson"  # same file already uploaded
WS_COL = "White Space Score"
CS_COL = "Client Market Share"
COMP_COL = "Competitor Strength"
SALES_COL = "ERP GT Sales Coverage"


# ———————————————————
# Data loaders (cached)
# ———————————————————
@st.cache_data(show_spinner="Loading MT White-Space data …")
def load_mt():
    if not Path(MT_FILE).exists():
        st.error(f"❌ {MT_FILE} not found")
        st.stop()
    df = pd.read_excel(MT_FILE)

    # rename / strip
    df.columns = df.columns.str.strip()
    df["County"] = df["County"].astype(str).str.title().str.strip()
    if "Brand" not in df.columns and "BRAND" in df.columns:
        df.rename(columns={"BRAND": "Brand"}, inplace=True)
    df["Brand"] = df["Brand"].astype(str).str.title().str.strip()

    # key used by choropleth
    df["COUNTY_KEY"] = df["County"]
    # numeric guards
    for c in [WS_COL, CS_COL, COMP_COL, SALES_COL]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        else:
            st.error(f"Column “{c}” missing in {MT_FILE}")
            st.stop()

    return df


@st.cache_data(show_spinner="Loading Kenya county GeoJSON …")
def load_county_geo():
    if not Path(COUNTY_GJ).exists():
        st.error(f"❌ {COUNTY_GJ} not found")
        st.stop()
    geo = json.loads(Path(COUNTY_GJ).read_text("utf-8"))
    # normalise the name field to COUNTY_KEY
    for feat in geo["features"]:
        nm = feat["properties"].get("COUNTY_NAM") or feat["properties"].get("NAME", "")
        feat["properties"]["COUNTY_KEY"] = str(nm).title().strip()
    return geo


MT_DF = load_mt()
COUNTY_GEO = load_county_geo()

# ———————————————————
# Helper: percent formatter
percent_fmt = lambda s: (s * 100 if s.max() <= 1 else s).round(2)


# ———————————————————
def page_mt_dashboard():
    st.markdown("## MT Dashboard – County Summary")

    # ── FILTERS
    f_brand, f_cnty, _ = st.columns([1, 1, 6])
    brand_sel = f_brand.selectbox("Brand", ["All"] + sorted(MT_DF["Brand"].unique()))
    cnty_sel = f_cnty.selectbox("County", ["All"] + sorted(MT_DF["County"].unique()))

    view = MT_DF.copy()
    if brand_sel != "All":
        view = view[view["Brand"] == brand_sel]
    if cnty_sel != "All":
        view = view[view["County"] == cnty_sel]

    # ── KPI CARDS
    k1, k2, k3 = st.columns(3)

    def card(col, title, value):
        col.markdown(
            f"<div style='border:1px solid #ccc;border-radius:10px;"
            f"padding:1rem;background:#253348;height:160px;'>"
            f"<h5 style='margin:0;color:#fff'>{title}</h5>"
            f"<p style='font-size:1.3rem;color:#fff'>{value}</p></div>",
            unsafe_allow_html=True,
        )

    card(k1, "White Space Score", f"{view[WS_COL].mean():.0f}")
    card(k2, "Client Market Share", f"{percent_fmt(view[CS_COL]).mean():.1f}%")
    card(k3, "Competitor Strength", f"{percent_fmt(view[COMP_COL]).mean():.1f}%")

    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

    # ── LAYOUT : map + bars
    left, _, right = st.columns([2, 0.1, 1])

    # —— Choropleth map ——
    with left:
        base = MT_DF if brand_sel == "All" else MT_DF[MT_DF["Brand"] == brand_sel]
        agg_ws = base.groupby("COUNTY_KEY", as_index=False)[WS_COL].mean()
        keys_full = [f["properties"]["COUNTY_KEY"] for f in COUNTY_GEO["features"]]
        mdf = (
            pd.DataFrame({"COUNTY_KEY": keys_full})
            .merge(agg_ws, how="left")
            .fillna({WS_COL: 0})
        )
        mdf["plot_ws"] = mdf[WS_COL]
        if cnty_sel != "All":
            mdf.loc[mdf["COUNTY_KEY"] != cnty_sel, "plot_ws"] = 0

        fig_map = px.choropleth_mapbox(
            mdf,
            geojson=COUNTY_GEO,
            locations="COUNTY_KEY",
            featureidkey="properties.COUNTY_KEY",
            color="plot_ws",
            color_continuous_scale="YlOrRd",
            range_color=(0, 60),
            mapbox_style="carto-positron",
            center={"lat": 0.23, "lon": 37.9},
            zoom=5.5,
            opacity=0.9,
            height=520,
        )
        # optional blue overlay for brand look
        fig_map.update_layout(
            mapbox=dict(
                layers=[
                    dict(
                        sourcetype="geojson",
                        type="fill",
                        below="traces",
                        source={
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": [
                                            [
                                                [10, -35],
                                                [70, -35],
                                                [70, 25],
                                                [10, 25],
                                                [10, -35],
                                            ]
                                        ],
                                    },
                                }
                            ],
                        },
                        color="rgba(0,120,255,0.15)",
                    )
                ]
            ),
            paper_bgcolor=NAVY_BG,
            plot_bgcolor=NAVY_BG,
            font_color=FG_TEXT,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # —— Right-hand bar panels ——
    with right:
        share = (
            (MT_DF if brand_sel == "All" else MT_DF[MT_DF["Brand"] == brand_sel])
            .groupby("County", as_index=False)[[CS_COL, COMP_COL]]
            .mean()
        )
        share[CS_COL] = percent_fmt(share[CS_COL])
        share[COMP_COL] = percent_fmt(share[COMP_COL])
        op = [
            1 if (cnty_sel == "All" or c == cnty_sel) else 0.3 for c in share["County"]
        ]

        fig_stack = go.Figure()
        fig_stack.add_bar(
            name="Client Share",
            x=share["County"],
            y=share[CS_COL],
            marker_opacity=op,
            marker_color="#00B4D8",
        )
        fig_stack.add_bar(
            name="Competitor Strength",
            x=share["County"],
            y=share[COMP_COL],
            marker_opacity=op,
            marker_color="#0077B6",
        )
        fig_stack.update_layout(
            barmode="stack",
            bargap=0.15,
            height=260,
            title="Market Composition",
            paper_bgcolor=PANEL_BG,
            plot_bgcolor=PANEL_BG,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=AXIS,
            yaxis=AXIS,
            legend=dict(
                bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=-0.25
            ),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        sales = (
            (MT_DF if brand_sel == "All" else MT_DF[MT_DF["Brand"] == brand_sel])
            .groupby("County", as_index=False)[SALES_COL]
            .sum()
        )
        sales_op = [
            1 if (cnty_sel == "All" or c == cnty_sel) else 0.3 for c in sales["County"]
        ]
        fig_sales = go.Figure(
            go.Bar(
                x=sales["County"],
                y=sales[SALES_COL],
                marker_opacity=sales_op,
                marker_color="#48CAE4",
            )
        )
        fig_sales.update_layout(
            height=260,
            title="ERP GT Sales Coverage",
            paper_bgcolor=PANEL_BG,
            plot_bgcolor=PANEL_BG,
            bargap=0.15,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=AXIS,
            yaxis=AXIS,
            showlegend=False,
        )
        st.plotly_chart(fig_sales, use_container_width=True)

    # ── Data table
    st.markdown("### Full MT Dataset")
    st.dataframe(MT_DF, height=350, use_container_width=True)
    st.caption(
        "Data: MT White-Space Score (cleaned)  ▪  Geometry: Kenya Counties GeoJSON"
    )


# ────────────────────────────  NEW PAGE  ────────────────────────────
#  Competitor Analysis  (Power-BI embeds)
#  • Paste anywhere ABOVE the PAGE_FUNCS dict in your main file
#  • Then add one line:  PAGE_FUNCS["Competitor Analysis"] = page_competitor_analysis
# ─────────────────────────────────────────────────────────────────────


def page_competitor_analysis() -> None:
    """
    Two-tab Power-BI viewer (Nielsen + Modern Trade).
    Compatible with your custom navbar pattern.
    """

    import streamlit as st
    import streamlit.components.v1 as components

    # ── Helper kept INSIDE the page function → no NameError ──────────
    def _dashboard_card(title: str, url: str) -> None:
        st.subheader(title)
        components.iframe(url, height=750, scrolling=True)

    # ── Power-BI report URLs -----------------------------------------
    NIELSEN_PBI_URL = (
        "https://app.powerbi.com/view?"
        "r=eyJrIjoiNGE5NDc5YjMtZWI4Yy00ZmY0LWI1ZjYtZmEwMTJjYTA1MWZkIiwidCI6"
        "IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9"
    )
    MT_PBI_URL = (
        "https://app.powerbi.com/view?"
        "r=eyJrIjoiYTZlNWYxNjctZDRjMS00NTA1LTkzNWItOWZmYWE3ZjY3MDJkIiwidCI6"
        "IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9&pageName=ReportSection"
    )

    # ── Simple tab dictionary ----------------------------------------
    TABS = {
        "📈 Nielsen": lambda: _dashboard_card("Nielsen Dashboard", NIELSEN_PBI_URL),
        "🏬 Modern Trade": lambda: _dashboard_card(
            "Modern-Trade Dashboard", MT_PBI_URL
        ),
    }

    # ── Active-tab state (uses query param ?tab=) --------------------
    if "comp_active_tab" not in st.session_state:
        st.session_state.comp_active_tab = list(TABS)[0]  # default first tab
    if "tab" in st.query_params and st.query_params["tab"] in TABS:
        st.session_state.comp_active_tab = st.query_params["tab"]

    # ── Navbar renderer ----------------------------------------------
    def _render_navbar() -> None:
        current = st.session_state.comp_active_tab
        html = '<div style="display:flex;gap:14px;margin:0.5rem 0 1.5rem;">'
        for tb in TABS:
            cls = (
                "background:#e5f1f8;border:1px solid #0278b7;"
                if tb == current
                else "background:transparent;"
            )
            html += (
                f'<button name="tab" value="{tb}" class="stButton" '
                f'style="padding:6px 20px;border-radius:18px;{cls}">{tb}</button>'
            )
        html += "</div>"
        st.markdown(f'<form method="get">{html}</form>', unsafe_allow_html=True)

    # ── Page header + navbar + content --------------------------------
    st.markdown(
        "<h2 style='margin-bottom:0.2rem'>Competitor Analysis</h2>",
        unsafe_allow_html=True,
    )
    _render_navbar()
    TABS[st.session_state.comp_active_tab]()  # draw the chosen report


# ╭───────────────────────────────  NAVIGATION  ─────────────────────╮
PAGE_FUNCS = {
    "README / Guide": page_readme,
    "Main Dashboard": page_main_dashboard,
    "Territory Deep Dive": page_territory_deep_dive,
    "SKU-Level Analysis": page_sku_dashboard,
    "Kenya Distributor Opportunity": page_kenya_dashboard,
    "Download Detail Report": page_opportunity_dashboard,
    "Competitor Analysis": page_competitor_analysis,
}

st.set_page_config(page_title="Dashboard", layout="wide")

# Load external CSS

# Initialize current page if not set
if "current_page" not in st.session_state:
    st.session_state.current_page = "README / Guide"

# Check for page update from query params (modern way)
query_params = st.query_params
if "page" in query_params:
    selected_page = query_params["page"]
    if selected_page in PAGE_FUNCS:
        st.session_state.current_page = selected_page


# Render the navbar
def navbar():
    current = st.session_state.current_page
    html = '<div class="navbar"><form method="get">'
    for page_name in PAGE_FUNCS.keys():
        class_name = "nav-btn active" if current == page_name else "nav-btn"
        html += f'<button name="page" value="{page_name}" class="{class_name}">{page_name}</button>'
    html += "</form></div>"
    st.markdown(html, unsafe_allow_html=True)


navbar()

# Render the active page function
PAGE_FUNCS[st.session_state.current_page]()
