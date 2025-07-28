import streamlit as st

def page_competitor_analysis() -> None:
    """
    Two-tab Power-BI viewer (Nielsen + Modern Trade).
    Compatible with your custom navbar pattern.
    """

    
    import streamlit.components.v1 as components

    # ── Helper kept INSIDE the page function → no NameError ──────────
    def _dashboard_card(title: str, url: str) -> None:
        st.subheader(title)
        components.iframe(url, height=750, scrolling=True)

    # ── Power-BI report URLs -----------------------------------------
    NIELSEN_PBI_URL = (
        "https://app.powerbi.com/view?"
        "r=eyJrIjoiNGE5NDc5YjMtZWI4Yy00ZmY0LWI1ZjYtZmEwMTJjYTA1MWZkIiwidCI6"
        "IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9"
    )
    MT_PBI_URL = (
        "https://app.powerbi.com/view?"
        "r=eyJrIjoiYTZlNWYxNjctZDRjMS00NTA1LTkzNWItOWZmYWE3ZjY3MDJkIiwidCI6"
        "IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9&pageName=ReportSection"
    )

    # ── Simple tab dictionary ----------------------------------------
    TABS = {
        "📈 Nielsen": lambda: _dashboard_card("Nielsen Dashboard", NIELSEN_PBI_URL),
        "🏬 Modern Trade": lambda: _dashboard_card(
            "Modern-Trade Dashboard", MT_PBI_URL
        ),
    }

    # ── Active-tab state (uses query param ?tab=) --------------------
    if "comp_active_tab" not in st.session_state:
        st.session_state.comp_active_tab = list(TABS)[0]  # default first tab
    if "tab" in st.query_params and st.query_params["tab"] in TABS:
        st.session_state.comp_active_tab = st.query_params["tab"]

    # ── Navbar renderer ----------------------------------------------
    def _render_navbar() -> None:
        current = st.session_state.comp_active_tab
        html = '<div style="display:flex;gap:14px;margin:0.5rem 0 1.5rem;">'
        for tb in TABS:
            cls = (
                "background:#e5f1f8;border:1px solid #0278b7;"
                if tb == current
                else "background:transparent;"
            )
            html += (
                f'<button name="tab" value="{tb}" class="stButton" '
                f'style="padding:6px 20px;border-radius:18px;{cls}">{tb}</button>'
            )
        html += "</div>"
        st.markdown(f'<form method="get">{html}</form>', unsafe_allow_html=True)

    # ── Page header + navbar + content --------------------------------
    st.markdown(
        "<h2 style='margin-bottom:0.2rem'>Competitor Analysis</h2>",
        unsafe_allow_html=True,
    )
    _render_navbar()
    TABS[st.session_state.comp_active_tab]()  # draw the chosen report