import plotly.express as px
import pandas as pd
from constants import gc,dc
from constants import data_reader_constants as drc

def rtm_hot_zones(rtm,level,selected_range):
    if level == "County":
        geo_src, id_field, key_col = drc.COUNTY_GEO, "COUNTY_KEY", "County"
    else:
        # detect sub-county column automatically
        def _match(c):
            return "sub" in c.lower() and "county" in c.lower()

        key_col = next((c for c in rtm.columns if _match(c)), None)
        if key_col is None:
            raise ValueError("Sub-county column not found in RTM data.")
        geo_src, id_field = drc.SUBCOUNTY_GEO, "SUB_KEY"

    # full list of polygons to colour (Kenya map)
    all_keys = [f["properties"][id_field] for f in geo_src["features"]]

    # Add AWS_Bin column (if not already done)
    aws_bins = [0, 20, 40, 60, 80, 100]
    aws_labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]
    rtm["AWS_Bin"] = pd.cut(
        rtm[gc.AWS], bins=aws_bins, labels=aws_labels, include_lowest=True, right=False
    )

    # Get selected AWS bin from session_state
    # selected_range = st.session_state.get("aws_range", "All")

    # Merge AWS value into map
    map_df = pd.DataFrame({id_field: all_keys}).merge(
        rtm[[key_col, gc.AWS, "AWS_Bin"]].rename(columns={key_col: id_field}),
        how="left",
    )

    # Filter map data based on selected bin
    if selected_range != "All":
        map_df["visible"] = map_df["AWS_Bin"] == selected_range
        map_df.loc[~map_df["visible"], gc.AWS] = 0  # or np.nan for total hide
    else:
        map_df["visible"] = True

    map_df = map_df.fillna({gc.AWS: 0})

    mfig = px.choropleth_mapbox(
        map_df,
        geojson=geo_src,
        locations=id_field,
        featureidkey=f"properties.{id_field}",
        color=gc.AWS,
        color_continuous_scale="YlOrRd",
        range_color=(0, 100),
        mapbox_style="carto-positron",
        center={"lat": 0.23, "lon": 37.9},
        zoom=5,
        opacity=0.9,
        height=520,
    )

    mfig.update_layout(margin=dict(l=0, r=0, t=10, b=10))
    return mfig




def aws_histogram(rtm,  aws_labels):
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
        yaxis=gc.AXIS,
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
    return hist

