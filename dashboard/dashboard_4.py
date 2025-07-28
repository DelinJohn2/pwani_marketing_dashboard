import streamlit as st
import pandas as pd
import pathlib
from data_viz import gt_data, percentage_data,executive_summary_retirver,extract_territory_block,extract_data, get_top_location,text_extractor,Population_percentage_per_brand,average_ws

def page_opportunity_dashboard():
    
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