import streamlit as st
from streamlit_plotly_events import plotly_events
import plotly.express as px
import streamlit as st
import pandas as pd
from utils import percent
from data_viz import rtm_hot_zones,aws_histogram
from constants import dc, gc
from constants import data_reader_constants as drc





def page_territory_deep_dive():
    """
    Detailed RTM drill-down.
    • Territory filter now includes “All”.
    • Map has no grey-blur or highlight layers – just coloured polygons
      wherever data exists.
    • Charts fill the Streamlit column via use_container_width=True.
    """
   

    st.markdown("## Territory Deep-Dive")

    c1, c2, c3 = st.columns([1, 1, 1])
    territory = c1.selectbox("Territory", ["All"] + sorted(drc.GT_DF["Territory"].unique()))
    brand_list = ["All"] + sorted(drc.GT_DF["Brand"].unique())
    default_brand_idx = (
        brand_list.index("Ushindi Bar") if "Ushindi Bar" in brand_list else 0
    )
    brand = c2.selectbox("Brand", brand_list, index=default_brand_idx)
    level_options = ["County", "Sub-County"]
    level = c3.selectbox(
        "Map granularity", level_options, index=level_options.index("Sub-County")
    )  # default to Sub-County)

    # ───── 4 ▸ KPI CARDS ----------------------------------------------------
    view_df = drc.GT_DF.copy()
    if territory != "All":
        view_df = view_df[view_df["Territory"] == territory]
    if brand != "All":
        view_df = view_df[view_df["Brand"] == brand]

    k1, k2, k3, k4 = st.columns(4)
    for box, title, value in zip(
        [k1, k2, k3, k4],
        ["Total Sales", "Market Share", "Competitor Strength", "White Space"],
        [
            f"{view_df[gc.SALES].sum():,.0f}",
            f"{percent(view_df[gc.CS]).mean():.1f}%",
            f"{percent(view_df[gc.COMP]).mean():.1f}%",
            f"{view_df[gc.WS].mean():.0f}",
        ],
    ):
        box.markdown(
            f"""<div class="kpiCardStyle"><h5>{title}</h5><p>{value}</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")  # spacer line

    # ───── 5 ▸ FILTER RTM ROWS --------------------------------------------
    rtm = drc.RTM_DF.copy()
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
        selected_range = st.session_state.get("aws_range", "All")

        
        st.plotly_chart(rtm_hot_zones(rtm,level,selected_range), use_container_width=True)

    # ───── 7 ▸ AWS HISTOGRAM ----------------------------------------------

    with right:
        st.markdown("### AWS Score Distribution")

        aws_bins = [0, 20, 40, 60, 80, 100]
        aws_labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]

        rtm = rtm.copy()
        rtm[gc.AWS] = pd.to_numeric(rtm[gc.AWS], errors="coerce")
        rtm["AWS_Bin"] = pd.cut(
            rtm[gc.AWS], bins=aws_bins, labels=aws_labels, include_lowest=True, right=False
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
        hist = aws_histogram(rtm, aws_labels)

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

