import streamlit as st
st.set_page_config(page_title="Dashboard", layout="wide")
from dashboard import page_main_dashboard, page_territory_deep_dive, page_sku_dashboard, page_opportunity_dashboard,page_competitor_analysis,page_readme




PAGE_FUNCS = {
    "README / Guide": page_readme,
    "Main Dashboard": page_main_dashboard,
    "Territory Deep Dive": page_territory_deep_dive,
    "SKU-Level Analysis": page_sku_dashboard,

    "Download Detail Report": page_opportunity_dashboard,
    "Competitor Analysis": page_competitor_analysis,
}



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
