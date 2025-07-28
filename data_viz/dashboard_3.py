from utils import colour_for
import plotly.graph_objs as go
import json
import plotly.express as px
import geopandas as gpd
from sklearn.cluster import KMeans
import pandas as pd

from constants import dc, gc



def load_map():
    poly = gpd.read_file(dc.GEO_FILE).rename(
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

def draw_cluster_map(df):
    cent,poly = load_map()
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
        paper_bgcolor=gc.PANEL_BG,
        plot_bgcolor=gc.PANEL_BG,
    )
    return fig


def cluster_share(gt_filt):
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
        paper_bgcolor=gc.PANEL_BG,
        plot_bgcolor=gc.PANEL_BG,
        showlegend=False,
        margin=dict(l=0, r=0, t=5, b=5),
    )
    return fig

def ped_vs_sales(gt_filt):
   
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
                paper_bgcolor=gc.PANEL_BG,
                plot_bgcolor=gc.PANEL_BG,
                margin=dict(l=0, r=0, t=5, b=5),
            )
            return fig
        else:
            raise ValueError("No PED & Sales rows in the filtered data.")
        


def price_buckets(rtm_filt):
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
            paper_bgcolor=gc.PANEL_BG,

            plot_bgcolor=gc.PANEL_BG,
            showlegend=False,
            margin=dict(l=30, r=10, t=30, b=20),
        )
        return fig
    else:
        raise ValueError("Not enough price variation in RTM data for clustering.")