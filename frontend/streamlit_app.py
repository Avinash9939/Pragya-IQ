import sys
import os
import json
from pathlib import Path

# Add project root to sys.path to allow frontend package resolution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from frontend.services import api_client
from frontend.components.sidebar import render_sidebar
from frontend.utils.session import is_logged_in, get_current_user

remembered_emails_file = project_root / "frontend" / "remembered_emails.json"

def load_remembered_emails():
    if remembered_emails_file.exists():
        try:
            with open(remembered_emails_file, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_remembered_email(email):
    if not email:
        return
    emails = load_remembered_emails()
    if email not in emails:
        emails.append(email)
        try:
            with open(remembered_emails_file, "w") as f:
                json.dump(emails, f)
        except Exception:
            pass


def clean_html(html_str: str) -> str:
    return "".join(l.strip() for l in html_str.split("\n") if l.strip())


# Page configuration
st.set_page_config(
    page_title="Pragya IQ - Business Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme-aware constants ──────────────────────────────────────
_current_theme = st.session_state.get("theme", "light")
_is_light = (_current_theme == "light")

# Background and text tokens
_bg_app = "#F8FAFC" if _is_light else "#07080F"
_bg_gradient_1 = "rgba(124, 92, 246, 0.06)" if _is_light else "rgba(124, 92, 246, 0.12)"
_bg_gradient_2 = "rgba(217, 70, 239, 0.04)" if _is_light else "rgba(217, 70, 239, 0.10)"
_text_primary = "#1E293B" if _is_light else "#FFFFFF"
_text_secondary = "rgba(30,41,59,0.75)" if _is_light else "rgba(255,255,255,0.85)"
_card_bg = "rgba(255,255,255,0.85)" if _is_light else "rgba(15, 8, 29, 0.75)"
_card_border = "rgba(0,0,0,0.08)" if _is_light else "rgba(168, 85, 247, 0.25)"
_card_shadow = "0 10px 30px rgba(0,0,0,0.08)" if _is_light else "0 10px 30px rgba(0,0,0,0.4)"

st.markdown(f"""
<style>
    /* Position the page titles closer to the top */
    div.block-container {{
        padding-top: 1.5rem !important;
        margin-top: 0px !important;
    }}
    
    /* Theme-aware stApp container */
    .stApp {{
        background-color: {_bg_app} !important;
        background-image:
            radial-gradient(at 0% 0%, {_bg_gradient_1} 0px, transparent 50%),
            radial-gradient(at 100% 100%, {_bg_gradient_2} 0px, transparent 50%) !important;
        background-attachment: fixed !important;
    }}
    
    /* Theme-aware login card */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {_card_bg} !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid {_card_border} !important;
        border-radius: 12px !important;
        padding: 6px 8px !important;
        box-shadow: {_card_shadow} !important;
        max-width: 260px !important;
        width: 260px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    
    /* Remove borders, backgrounds from forms */
    div[data-testid="stForm"], [data-testid="stForm"] {{
        background: transparent !important;
        backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}

    /* Theme toggle button */
    .theme-toggle-btn {{
        background: {'rgba(0,0,0,0.05)' if _is_light else 'rgba(255,255,255,0.08)'};
        border: 1px solid {'rgba(0,0,0,0.12)' if _is_light else 'rgba(255,255,255,0.15)'};
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.1rem;
        transition: all 0.2s ease;
    }}
    .theme-toggle-btn:hover {{
        background: {'rgba(0,0,0,0.1)' if _is_light else 'rgba(255,255,255,0.15)'};
        transform: scale(1.1);
    }}
</style>
""", unsafe_allow_html=True)

if is_logged_in():
    pg = st.navigation([
        st.Page("pages/1_Upload_Data.py", title="Upload Data", icon="📤"),
        st.Page("pages/2_Prepare_Data.py", title="Prepare Data", icon="🔧"),
        st.Page("pages/3_KPI_Dashboard.py", title="KPI Dashboard", icon="📊"),
        st.Page("pages/4_Forecasting.py", title="Forecasting", icon="🔮"),
        st.Page("pages/5_Customers.py", title="Customer Intelligence", icon="👥"),
        st.Page("pages/6_Anomalies_And_Explainability.py", title="Anomaly Detection", icon="🚨"),
        st.Page("pages/7_🤖_AI_Business_Copilot.py", title="Pragya AI", icon="🤖"),
        st.Page("pages/9_Admin.py", title="Admin Console", icon="🛡️")
    ], position="hidden")
    
    # Render global unified sidebar AFTER router configures the registry
    render_sidebar()
    
    pg.run()
else:
    # Render sidebar for login screen (it will be empty but properly hooked)
    render_sidebar()

    # Inject compact CSS override for login view to prevent scroll and reduce heights
    st.markdown(f"""
    <style>
        /* Force single viewport layout on login page */
        html, body, [data-testid="stAppViewContainer"], .stApp {{
            overflow: hidden !important;
            height: 100vh !important;
            max-height: 100vh !important;
        }}
        
        /* Adjust layout spacing on the login container */
        div.block-container {{
            padding-top: 0.8rem !important;
            padding-bottom: 0.4rem !important;
            height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            margin-left: auto !important;
            margin-right: auto !important;
            max-width: 100% !important;
        }}
        
        /* Centered display of columns */
        div[data-testid="stHorizontalBlock"] {{
            align-items: center !important;
        }}

        /* Compact feature card height and padding */
        .feature-card {{
            height: 110px !important;
            padding: 10px 10px !important;
        }}
        .feature-icon-wrapper {{
            width: 32px !important;
            height: 32px !important;
            margin-bottom: 4px !important;
        }}
        .feature-title {{
            font-size: 0.80rem !important;
            margin-bottom: 2px !important;
        }}
        .feature-desc {{
            font-size: 0.68rem !important;
            line-height: 1.15 !important;
        }}

        /* Compact login card */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 10px 14px !important;
            max-width: 250px !important;
            width: 250px !important;
        }}

        /* Compact elements inside login card */
        div[data-testid="stVerticalBlockBorderWrapper"] input {{
            padding-top: 2px !important;
            padding-bottom: 2px !important;
            height: 26px !important;
            font-size: 0.78rem !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"]>div {{
            height: 24px !important;
            font-size: 0.78rem !important;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            min-height: auto !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] label,
        div[data-testid="stVerticalBlockBorderWrapper"] p,
        div[data-testid="stVerticalBlockBorderWrapper"] span {{
            font-size: 0.78rem !important;
            line-height: 1.25 !important;
        }}
        
        /* Reduce margins below header and headers on login page */
        .landing-footer {{
            margin-top: 15px !important;
            padding-bottom: 12px !important;
            text-align: center !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "🔑 Sign In / Login"

    is_login = (st.session_state["auth_tab"] == "🔑 Sign In / Login")

    # Split Column Welcome Layout (Left content & Right login card)
    left_side, right_side = st.columns([6.2, 3.8], gap="large")
    
    with left_side:
        # Left branding header
        st.markdown(f"""
            <div style="display:flex; align-items:center; margin-bottom:0.6rem; margin-top:2px;">
                <svg viewBox="0 0 100 100" width="34" height="34" stroke="none" fill="none" style="display:inline-block; vertical-align:middle; margin-right:10px;">
                    <defs>
                        <linearGradient id="brand-radial-left-decor" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#7C3AED"/>
                            <stop offset="100%" stop-color="#3B82F6"/>
                        </linearGradient>
                    </defs>
                    <circle cx="50" cy="50" r="46" fill="url(#brand-radial-left-decor)"/>
                    <path d="M35 50 C35 38, 42 32, 50 32 C58 32, 65 38, 65 50 C65 62, 58 68, 50 68 C42 68, 35 62, 35 50 Z" stroke="#ffffff" stroke-width="3.5" fill="none" opacity="0.9"/>
                    <path d="M50 32 V68" stroke="#ffffff" stroke-width="3.5" fill="none" opacity="0.9"/>
                    <circle cx="50" cy="38" r="4" fill="#ffffff"/>
                    <circle cx="50" cy="62" r="4" fill="#ffffff"/>
                    <circle cx="42" cy="50" r="4" fill="#ffffff"/>
                    <circle cx="58" cy="50" r="4" fill="#ffffff"/>
                    <path d="M42 50 Q50 45 58 50" stroke="#ffffff" stroke-width="2.5" fill="none"/>
                </svg>
                <div style="display:inline-block; vertical-align:middle; text-align:left;">
                    <div style="font-weight: 800; font-size:1.35rem; color:{_text_primary}; letter-spacing:0.04em; line-height:1.2;">PRAGYA IQ</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Left titles block
        st.markdown(f"""
            <div style="margin-top:0.8rem; margin-bottom:0.8rem; text-align:left;">
                <h1 style="font-size:2.0rem; font-weight:900; line-height:1.15; margin:0 0 0.5rem 0; font-family:'Inter', sans-serif;">
                    <span style="background: linear-gradient(90deg, #2563EB 0%, #4F46E5 25%, #7C3AED 50%, #A855F7 75%, #EC4899 100%) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; background-clip: text !important; color: transparent !important; filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.35)) !important; display:inline-block;">AI-Powered</span><br/>
                    <span style="color:{_text_primary};">Business Intelligence Platform</span>
                </h1>
                <div style="font-size:0.85rem; color:{_text_secondary}; font-weight:500; font-family:'Inter', sans-serif; margin-bottom:0.4rem;">
                    Decision Support &amp; Business Intelligence System
                </div>
                <div style="font-size:0.75rem; color:#2DD4BF; font-weight:600; font-style:italic; font-family:'Inter', sans-serif; margin-top:2px;">
                    "Every Dataset Has a Story. Ask Pragya IQ"
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Left features block (3 columns horizontally)
        feat_col1, feat_col2, feat_col3 = st.columns(3, gap="small")
        with feat_col1:
            st.markdown("""
                <div class="feature-card">
                    <div class="feature-icon-wrapper">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.2" fill="none">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                    </div>
                    <div class="feature-title">Secure &amp; Reliable</div>
                    <div class="feature-desc">Enterprise-grade security for your data</div>
                </div>
            """, unsafe_allow_html=True)
            
        with feat_col2:
            st.markdown("""
                <div class="feature-card">
                    <div class="feature-icon-wrapper">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.2" fill="none">
                            <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
                            <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
                            <path d="M12 5v14"/>
                        </svg>
                    </div>
                    <div class="feature-title">AI-Powered Insights</div>
                    <div class="feature-desc">Advanced AI models for smarter decisions</div>
                </div>
            """, unsafe_allow_html=True)
            
        with feat_col3:
            st.markdown("""
                <div class="feature-card">
                    <div class="feature-icon-wrapper">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.2" fill="none">
                            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                        </svg>
                    </div>
                    <div class="feature-title">Real-time Analytics</div>
                    <div class="feature-desc">Get real-time insights and stay ahead</div>
                </div>
            """, unsafe_allow_html=True)

    with right_side:
        # Theme toggle (crescent moon) at top-right
        _moon_bg = 'rgba(0,0,0,0.04)' if _is_light else 'rgba(255,255,255,0.08)'
        _moon_border = 'rgba(0,0,0,0.10)' if _is_light else 'rgba(255,255,255,0.12)'
        _moon_fill = '#64748B' if _is_light else '#FCD34D'
        _theme_toggle_col1, _theme_toggle_col2 = st.columns([9, 1])
        with _theme_toggle_col2:
            if st.button("🌙", key="login_moon_toggle", help="Toggle Light / Dark theme"):
                st.session_state["theme"] = "dark" if _is_light else "light"
                st.rerun()

        # Login Glass Card
        with st.container(border=True):
            if is_login:
                st.markdown('<div class="landing-login-title" style="text-align:center;">Welcome back!</div>', unsafe_allow_html=True)
                st.markdown('<div class="landing-login-sub" style="text-align:center;">Login to your account to continue</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="landing-login-title" style="text-align:center;">Create Account</div>', unsafe_allow_html=True)
                st.markdown('<div class="landing-login-sub" style="text-align:center;">Register a new profile to get started</div>', unsafe_allow_html=True)

            st.markdown(clean_html('<div class="select-action-divider"><span>SELECT ACTION</span></div>'), unsafe_allow_html=True)
            
            auth_tab = st.selectbox(
                "Select Action Dropdown", 
                ["🔑 Sign In / Login", "📝 Create Account / Register"], 
                label_visibility="collapsed",
                key="auth_tab_select"
            )
            
            # Sync session state
            if auth_tab != st.session_state["auth_tab"]:
                st.session_state["auth_tab"] = auth_tab
                st.rerun()

            if is_login:
                with st.container(border=False):
                    remembered_emails = load_remembered_emails()
                    last_email = remembered_emails[-1] if remembered_emails else ""
                    email = st.text_input("Email Address", value=last_email, placeholder="e.g. name@domain.com", key="login_email")
                    show_pwd = st.checkbox("Show password", key="login_show_pwd")
                    password = st.text_input("Password", type="default" if show_pwd else "password", placeholder="••••••••", key="login_pass")
                    
                    cb_col, link_col = st.columns(2)
                    with cb_col:
                        st.checkbox("Remember me", value=True, key="remember_me_check")
                    with link_col:
                        st.markdown('<div style="text-align: right; margin-top: 4px;"><a href="#" style="color:#7C3AED; text-decoration:none; font-size: 0.85rem;">Forgot password?</a></div>', unsafe_allow_html=True)
                    
                    st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)
                    submit = st.button("Sign In →", use_container_width=True, type="primary")
                    
                    if submit:
                        if not email or not password:
                            st.error("Please fill in all credentials.")
                        else:
                            try:
                                with st.spinner("Authenticating credentials..."):
                                    token = api_client.login(email, password)
                                if st.session_state.get("remember_me_check"):
                                    save_remembered_email(email)
                                st.balloons()
                                st.success("Login successful!")
                                st.rerun()
                            except api_client.ApiError as e:
                                st.error(f"❌ Login failed: {e.message}")
                            except Exception as e:
                                st.error(f"⚠️ Unexpected system error occurred: {str(e)}")
                                
                    if remembered_emails:
                        options_html = "".join([f'<option value="{e}"></option>' for e in remembered_emails])
                        jscode = f"""
                        <script>
                        const parentDoc = window.parent.document;
                        function setupDatalist() {{
                            const emailInput = parentDoc.querySelector('input[placeholder="e.g. name@domain.com"]');
                            if (emailInput) {{
                                emailInput.setAttribute('list', 'remembered-emails-list');
                                let datalist = parentDoc.getElementById('remembered-emails-list');
                                if (!datalist) {{
                                    datalist = parentDoc.createElement('datalist');
                                    datalist.id = 'remembered-emails-list';
                                    parentDoc.body.appendChild(datalist);
                                }}
                                datalist.innerHTML = '{options_html}';
                            }}
                        }}
                        setTimeout(setupDatalist, 200);
                        setTimeout(setupDatalist, 600);
                        setTimeout(setupDatalist, 1200);
                        </script>
                        """
                        import streamlit.components.v1 as components
                        components.html(jscode, height=0, width=0)
                                
                st.markdown(clean_html('<div class="or-divider"><span>OR</span></div>'), unsafe_allow_html=True)
                if st.button("🎧 Contact Admin for Access", use_container_width=True, type="secondary", key="btn_contact_admin"):
                    st.info("Please contact IT support or your administrator to request access credentials.")
                    
            else:
                with st.container(border=False):
                    email = st.text_input("Email Address", placeholder="e.g. name@domain.com", key="reg_email")
                    show_pwd2 = st.checkbox("Show password", key="reg_show_pwd")
                    password = st.text_input("Password", type="default" if show_pwd2 else "password", placeholder="Choose a secure password", key="reg_pass")
                    role = st.selectbox("Assigned Role", ["viewer", "analyst", "admin"], key="reg_role")
                    
                    st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)
                    submit = st.button("Register Account", use_container_width=True, type="primary")
                    
                    if submit:
                        if not email or not password:
                            st.error("Please specify both email and password parameters.")
                        elif len(password) < 6:
                            st.error("Password must be at least 6 characters long.")
                        else:
                            try:
                                with st.spinner("Creating account..."):
                                    api_client.register(email, password, role)
                                st.success("🎉 Registration complete! You can now switch to 'Sign In' and log in.")
                            except api_client.ApiError as e:
                                st.error(f"❌ Registration failed: {e.message}")
                            except Exception as e:
                                st.error(f"⚠️ Unexpected system error occurred: {str(e)}")

    # Footer section spaced below the column systems
    st.markdown("""
        <div class="landing-footer">
            &copy; 2026 Pragya IQ. All rights reserved.
        </div>
    """, unsafe_allow_html=True)
