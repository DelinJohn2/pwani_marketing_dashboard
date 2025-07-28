import streamlit as st


from data_viz import cluster_share,draw_cluster_map,ped_vs_sales,price_buckets

from constants import data_reader_constants as drc




# ───────── load map



# ───────── main page
def page_sku_dashboard():
    st.title("SKU-Cluster Dashboard")

    

    # FILTERS
    f = st.columns(5)
    market_sel = f[0].selectbox("Market", ["ALL"] + sorted(drc.gt["MARKET"].unique()))
    brand_sel = f[1].selectbox("Brand", ["ALL"] + sorted(drc.gt["BRAND"].unique()))
    cluster_sel = f[2].selectbox(
        "Cluster", ["ALL"] + sorted(drc.gt["CLUSTER"].dropna().astype(str).unique())
    )
    # SKU list from RTM after market & brand filter
    rtm_pool = drc.rtm.copy()
    if market_sel != "ALL":
        rtm_pool = rtm_pool[rtm_pool["MARKET"] == market_sel]
    if brand_sel != "ALL":
        rtm_pool = rtm_pool[rtm_pool["BRAND"] == brand_sel]
    sku_sel = f[3].selectbox(
        "SKU (price panel only)", ["ALL"] + sorted(rtm_pool["SKU"].dropna().unique())
    )

    period_sel = f[4].selectbox("Period", ["LAST 12 MONTHS"])

    # GT filters (SKU not applied)
    gt_filt = drc.gt.copy()
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
    rtm_filt = drc.rtm.copy()
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
        fig = cluster_share(gt_filt)
        st.plotly_chart(fig, use_container_width=True)

    # 2 Price buckets (SKU aware)
    with c2:
        st.subheader("Price Buckets (RTM)")
        if {"AVERAGE_BASE_PRICE", "VOLUME"}.issubset(rtm_filt.columns):
                fig= price_buckets(rtm_filt)
            
                st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("RTM price / volume columns missing.")

    # 3 PED vs sales (SKU ignored)
    with c3:
        st.subheader("PED vs Sales")
        if {"PED", "SALES_VAL"}.issubset(gt_filt.columns):
            fig=ped_vs_sales(gt_filt)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No PED & Sales rows.")
        else:
            st.info("Missing PED or SALES_VAL columns.")

    # 4 Map (SKU ignored)
    with c4:
        st.subheader("Territory Bubble Map")
        fig=draw_cluster_map(gt_filt)
        st.plotly_chart(fig, use_container_width=True)
