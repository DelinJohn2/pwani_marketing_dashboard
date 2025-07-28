import pandas as pd
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import add_zero_layer,percent




def gt_territory_map(df,brand,key,sel,geo):

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
        font_color= "#e3e8ef",
    )

    add_zero_layer(
        fig,
        geo,
        key,
        mdf.loc[mdf["White Space Score"] == 0, key].tolist(),
        "You are not selling here",
    )
    return fig




def gt_market_composition_bar(df,brand,region,sel):
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
        xaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        yaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.25, bgcolor="rgba(0,0,0,0)"
        ),
    )
    return stk

def gt_sales_bar_graph(brand,region,sel,df):
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
        xaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        yaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        showlegend=False,
    )

    return erp





