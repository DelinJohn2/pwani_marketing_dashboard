import streamlit as st
import plotly.graph_objects as go

import pandas as pd


percent = lambda s: (s * 100 if s.max() <= 1 else s).round(2)

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


def colour_for(cluster: str) -> str:
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

