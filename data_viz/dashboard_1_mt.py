import pandas as pd
import plotly.express as px
from utils import add_zero_layer,percent
from constants import gc
import plotly.graph_objects as go





def mt_territory_map(df,brand,sel,COUNTY_GEO):
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
        font_color="#e3e8ef",
    )
    add_zero_layer(
        fig_c,
        COUNTY_GEO,
        "COUNTY_KEY",
        mdf.loc[mdf["White Space Score"] == 0, "COUNTY_KEY"].tolist(),
        "Not present here",
    )
    fig_c.update_layout(legend=dict(traceorder="normal"))
    return fig_c



def draw_bubble_map(brand,sel,MT_CLUSTER_DF,COUNTY_GEO,COUNTY_CENTROIDS):
    df = MT_CLUSTER_DF.copy()
    if brand != "All":
        df = df[df["Brand"] == brand]
    if sel != "All":
        df = df[df["County"] == sel]
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
    COLOR_CLUSTERS = {
    "Green": "#2ECC71",
    "Blue": "#3498DB",
    "Yellow": "#F1C40F",
    "White": "#ECF0F1",
    "Purple": "#9B59B6",
    "Red": "#E74C3C",
}
    
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

        paper_bgcolor=gc.NAVY_BG,
        plot_bgcolor=gc.NAVY_BG,
        font_color=gc.FG_TEXT,
    )
    return fig


def mt_marker_composition(df,sel ):
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
        paper_bgcolor=gc.PANEL_BG,
        plot_bgcolor=gc.PANEL_BG,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=gc.AXIS | dict(tickangle=-45),
        yaxis=gc.AXIS,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"
        ),
    )
    return stack


def mt_sales_bar_graph(df,sel):
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
        paper_bgcolor=gc.PANEL_BG,
        plot_bgcolor=gc.PANEL_BG,
        bargap=0.15,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=gc.AXIS | dict(tickangle=-45),
        yaxis=gc.AXIS,
        showlegend=False,
    )
    return erp