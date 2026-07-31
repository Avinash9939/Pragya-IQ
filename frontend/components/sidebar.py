import streamlit as st
from frontend.utils.session import is_logged_in, get_current_user, logout
import os

# Triggered cache invalidate
@st.cache_data
def get_cached_css(css_path: str, mtime: float) -> str:
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def render_sidebar_header() -> None:
    """
    Renders page styling overrides and the top branding section of the sidebar.
    """
    # Inject static CSS stylesheet if present
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "styles.css")
    mtime1 = os.path.getmtime(css_path) if os.path.exists(css_path) else 0.0
    css_content = get_cached_css(css_path, mtime1)
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            
    # Inject light theme override if enabled
    if st.session_state.get("theme", "light") == "light":
        light_css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "light_theme.css")
        mtime2 = os.path.getmtime(light_css_path) if os.path.exists(light_css_path) else 0.0
        light_css_content = get_cached_css(light_css_path, mtime2)
        if light_css_content:
            st.markdown(f"<style>{light_css_content}</style>", unsafe_allow_html=True)

    # Dynamic visibility check: if not logged in, completely hide sidebar and stop rendering navigation
    if not is_logged_in():
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    display: none !important;
                }
                [data-testid="collapsedControl"] {
                    display: none !important;
                }
                .stApp {
                    margin-left: 0 !important;
                }
                div.block-container {
                    margin-left: auto !important;
                    margin-right: auto !important;
                    max-width: 100% !important;
                }
            </style>
        """, unsafe_allow_html=True)
        return

    # Branding Section
    st.sidebar.markdown("""
        <div class="sidebar-branding">
            <div class="sidebar-brand-container" style="display: flex; align-items: center;">
                <svg viewBox="0 0 24 24" width="32" height="32" stroke="#7C3AED" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" class="brand-logo-svg" style="margin-right:12px; filter: drop-shadow(0 0 8px #7C3AED); flex-shrink:0;">
                    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1 0-3.12 3 3 0 0 1 0-3.88 2.5 2.5 0 0 1 0-3.12A2.5 2.5 0 0 1 9.5 2Z"/>
                    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 0-3.12 3 3 0 0 0 0-3.88 2.5 2.5 0 0 0 0-3.12A2.5 2.5 0 0 0 14.5 2Z"/>
                </svg>
                <div class="brand-text-block" style="display: flex; flex-direction: column; align-items: flex-start; justify-content: center;">
                    <span class="sidebar-brand-name" style="font-weight: 800; color: #FFFFFF; font-size: 1.3rem; line-height: 1.1; letter-spacing: 0.02em;">PRAGYA IQ</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar_nav() -> None:
    """
    Renders core page links, logout button, and the footer card in the sidebar.
    """
    if not is_logged_in():
        return

    # Navigation Section
    st.sidebar.page_link("pages/1_Upload_Data.py", label="📤  Upload Data")
    st.sidebar.page_link("pages/2_Prepare_Data.py", label="🔧  Prepare Data")
    st.sidebar.page_link("pages/3_KPI_Dashboard.py", label="📊  KPI Dashboard")
    st.sidebar.page_link("pages/4_Forecasting.py", label="🔮  Forecasting")
    st.sidebar.page_link("pages/5_Customers.py", label="👥  Customer Intelligence")
    st.sidebar.page_link("pages/6_Anomalies_And_Explainability.py", label="🚨  Anomalies & Explainability")

    st.sidebar.markdown('<div class="sidebar-nav-divider"></div>', unsafe_allow_html=True)
    st.sidebar.page_link("pages/7_🤖_AI_Business_Copilot.py", label="🤖  Pragya AI")
    st.sidebar.page_link("pages/9_Admin.py", label="🛡️  Admin Console")

    # Theme Switcher
    theme_val = st.session_state.get("theme", "light")
    is_dark = st.sidebar.toggle("🌙 Dark Mode", value=(theme_val == "dark"), key="sidebar_theme_toggle")
    
    new_theme = "dark" if is_dark else "light"
    if new_theme != theme_val:
        st.session_state["theme"] = new_theme
        st.rerun()

    # In-menu Logout button
    st.sidebar.markdown('<div class="sidebar-nav-divider"></div>', unsafe_allow_html=True)
    if st.sidebar.button("⎋  Logout", key="sidebar_logout_btn_item", use_container_width=True, type="secondary"):
        logout()
        st.success("Successfully logged out.")
        st.rerun()

    # Footer Section
    st.sidebar.markdown("""
        <div class="sidebar-footer-card">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="#7C3AED" stroke-width="2.2" fill="none" class="sidebar-footer-icon" style="filter: drop-shadow(0 0 5px #7C3AED);">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <div class="sidebar-footer-text" style="display:inline-block; vertical-align:middle; text-align:left; margin-left:8px;">
                <div class="sidebar-footer-title" style="margin:0; padding:0; line-height:1.2; font-weight:750; color:#FFFFFF;">PRAGYA IQ</div>
                <div class="sidebar-footer-version" style="margin:0; padding:0; line-height:1.2; font-size:0.65rem; color:#A1A1AA;">Version 1.0.0</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> None:
    """
    Renders a unified navigation sidebar. Backward compatible for all other pages.
    """
    render_sidebar_header()
    render_sidebar_nav()
