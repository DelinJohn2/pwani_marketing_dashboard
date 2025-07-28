
from pathlib import Path
import streamlit as st
from utils import percent, spacer 
from constants import dc, gc
from constants import data_reader_constants as drc
from data_viz import draw_bubble_map,gt_territory_map,gt_market_composition_bar,gt_sales_bar_graph,mt_territory_map,mt_marker_composition,mt_sales_bar_graph


# Optional custom CSS
if Path("styles.css").exists():
    with open("styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def page_main_dashboard():
    st.markdown("## Main Dashboard")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        mode = st.selectbox("Data Source", ("GT – Territory View", "MT – County View"))
    is_mt = mode.startswith("MT")
    df, geo, region, key = (
        (drc.GT_DF, drc.TERR_GEO, "Territory", "TERR_KEY")
        if not is_mt
        else (drc.MT_DF, drc.COUNTY_GEO, "County", "COUNTY_KEY")
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


    if not is_mt:
        map_col, _, bar_col = st.columns([1.5, 0.01, 1])

        with map_col:
        
            st.plotly_chart(gt_territory_map(df,brand,key,sel,geo), use_container_width=False)

        with bar_col:
    
            st.plotly_chart(gt_market_composition_bar(df,brand,region,sel), use_container_width=True)
            st.plotly_chart(gt_sales_bar_graph(brand,region,sel,df), use_container_width=True)

        spacer()
        st.markdown("---")
        st.markdown("### Detailed Dataset")
        st.dataframe(df, height=350, use_container_width=True)
        spacer(20)

    else:  
        map_l, map_r = st.columns(2)

        with map_l:
            st.markdown("### MT White Space")
            fig_c = mt_territory_map(view, brand, sel, geo)
            st.plotly_chart(fig_c, use_container_width=True)

        with map_r:
            st.markdown("### Cluster Density by County")
            st.plotly_chart(draw_bubble_map(brand,sel,drc.MT_CLUSTER_DF,drc.COUNTY_GEO,drc.COUNTY_CENTROIDS), use_container_width=True)

        spacer()

        gcol, tcol = st.columns(2)

        with gcol:
            st.markdown("### Market and Sales")
            st.plotly_chart(mt_marker_composition(df,sel), use_container_width=True)
            st.plotly_chart(mt_sales_bar_graph(df,sel), use_container_width=True)

        with tcol:
            st.markdown("### Detailed Dataset")
            st.dataframe(df, height=520, use_container_width=True)
            st.caption(
                "Sources – GT KPI & Territory GeoJSON • MT KPI & Cluster Bubbles • Kenya County GeoJSON"
            )

        spacer(20)