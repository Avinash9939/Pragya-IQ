"""Consolidated AI Business Copilot landing page.

Fully designed home screen with a modern enterprise dark theme inspired by Microsoft Copilot,
with Vertically Centered welcoming layouts, metadata indicators, and a clean messaging interface.
"""
from __future__ import annotations

import html
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.components.auth_guard import require_login
from frontend.components.sidebar import render_sidebar
from frontend.services import api_client
from frontend.utils.formatting import format_currency, format_number, format_percentage

require_login()

# Configure the Streamlit page for a wide, immersive dashboard layout with custom tab titles.




# ══════════════════════════════════════════════════════════════
#  MS COPILOT STYLE SYSTEM & THEME
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* -------------------------------------------------------------
       GLOBAL TYPOGRAPHY & SPACING OVERRIDES
    -------------------------------------------------------------- */
    html, body, [class*="st-"], .stApp, .block-container, input, button, select, textarea {{
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }}
    
    /* Large bold headings */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-weight: 600 !important;
        letter-spacing: -0.03em !important;
        color: #F8FAFC !important;
        line-height: 1.15 !important;
        margin-bottom: 0.75rem !important;
    }}
    
    /* Small gray subtitles */
    p, span, .stMarkdown p {{
        color: #94A3B8;
        font-weight: 400;
        line-height: 1.7 !important;
    }}
    strong, b {{
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }}
    
    /* Premium spacing */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 900px !important;
        margin: 0 auto;
    }
    
    .stApp {{
        background-color: #0B0E14;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.15) 0%, transparent 60%),
            radial-gradient(circle at 85% 20%, rgba(59, 130, 246, 0.10) 0%, transparent 50%),
            radial-gradient(circle at 15% 90%, rgba(109, 40, 217, 0.12) 0%, transparent 50%);
        background-attachment: fixed;
    }}
    


    /* Fabric Copilot Insight Card */
    .fabric-insight-card {{
        background: rgba(18, 22, 33, 0.65);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 20px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 25px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        transition: all 0.4s ease;
    }}
    .fabric-insight-card:hover {{
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.12), 0 0 40px rgba(168, 85, 247, 0.15);
        border-color: rgba(168, 85, 247, 0.45);
        transform: translateY(-2px);
    }}
    .fabric-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .fabric-ai-brand {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #C4B5FD;
        font-size: 0.95rem;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }}
    .fabric-card-timestamp {
        color: #64748B;
        font-size: 0.8rem;
    }
    .fabric-card-title {
        color: #F8FAFC;
        font-size: 1.4rem;
        margin: 0 0 6px 0;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    .fabric-card-desc {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 15px;
    }
    .fabric-card-badge {
        display: inline-block;
        background: rgba(79, 140, 255, 0.15);
        color: #60A5FA;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 20px;
        border: 1px solid rgba(79, 140, 255, 0.3);
    }
    .fabric-card-body {
        color: #E2E8F0;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .fabric-card-body p { margin-top: 0; }
    
    /* Copilot Input Enhancements */
    .input-hint-text {
        position: absolute;
        right: 80px;
        top: 50%;
        transform: translateY(-50%);
        color: #64748B;
        font-size: 0.85rem;
        pointer-events: none;
    }
    
    /* Animated Send Button */
    .fabric-send-btn-wrap button {
        background: linear-gradient(135deg, #6D5DF6 0%, #4F8CFF 100%) !important;
        border-radius: 12px !important;
        position: relative;
        overflow: hidden;
        animation: pulse-glow 3s infinite alternate;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
    }
    .fabric-send-btn-wrap button:hover {
        background: linear-gradient(135deg, #4F8CFF 0%, #6D5DF6 100%) !important;
        transform: translateY(-1px) !important;
    }
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 10px rgba(109, 93, 246, 0.3); }
        100% { box-shadow: 0 0 20px rgba(79, 140, 255, 0.6); }
    }

</style>
""", unsafe_allow_html=True)


# Helper: Formulate response via Hybrid AI Engine
def get_hybrid_answer(query: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Reroutes user queries directly into the HybridCopilotEngine architecture
    to deterministically classify the intent and formulate responses using
    local Pandas analytics before deferring to Gemini.
    """
    active_id = st.session_state.get("active_dataset_id")
    if df is None or df.empty or not active_id:
        return {
            "content": "Please upload and prepare a dataset so I can run accurate analytical queries against it.",
            "type": "text"
        }
        
    try:
        from frontend.utils.hybrid_ai import HybridCopilotEngine
        engine = HybridCopilotEngine(df, api_client, active_id)
        return engine.process_query(query)
    except Exception as e:
        import traceback
        import sys
        print(f"HYBRID ENGINE ENCOUNTERED FATAL ERROR:\n{traceback.format_exc()}", file=sys.stderr)
        return {
            "content": f"**System Engine Failure:**\n\nCould not initialize Intelligence Engine. Ensure the dataset matches standard formatting. \n*Context:* {str(e)}",
            "type": "text"
        }


from frontend.utils.dataset_cache import load_dataframe

# Helper: Load analytical dataframe from user storage
def _read_active_dataframe(dataset_id: int) -> Optional[pd.DataFrame]:
    user = st.session_state.get("user", {})
    user_id = user.get("id")
    if not user_id:
        return None
    return load_dataframe(user_id, dataset_id)


if st.runtime.exists():
    # Load all datasets owned by user
    try:
        datasets = api_client.list_datasets(force_refresh=True)
    except Exception:
        datasets = []

    # Safe retrieval of session dataset selectors
    active_id = st.session_state.get("active_dataset_id")
    if datasets:
        options = {d["id"]: d for d in datasets}
        if active_id not in options:
            active_id = list(options.keys())[0]
            st.session_state["active_dataset_id"] = active_id
        active_dataset = options[active_id]
    else:
        active_dataset = None
        active_id = None

    # Load dataframe and gather metadata
    rows, cols, updated_str = "0", "0", "N/A"
    if active_id:
        df = _read_active_dataframe(active_id)
        if df is not None:
            rows = f"{len(df):,}"
            cols = str(len(df.columns))
            
            # Format update timestamp
            raw_time = active_dataset.get("updated_at") or active_dataset.get("created_at")
            if raw_time:
                try:
                    updated_str = pd.to_datetime(raw_time).strftime("%b %d, %Y %H:%M")
                except Exception:
                    updated_str = str(raw_time)[:16]

    # Scoped chat message persistence
    def _chat_key(suffix):
        return f"chat_{active_id}_{suffix}" if active_id else f"chat_none_{suffix}"

    if _chat_key("indexed") not in st.session_state:
        st.session_state[_chat_key("indexed")] = None
    if _chat_key("session_id") not in st.session_state:
        st.session_state[_chat_key("session_id")] = None

    import json
    import uuid
    from datetime import datetime

    def _load_history_state():
        return st.session_state.get("copilot_history_chats_state", [])

    def _save_history_state(chats):
        st.session_state["copilot_history_chats_state"] = chats

    # Initialize / Load multi-chat history
    all_chats = _load_history_state()
    chats_for_active_ds = [c for c in all_chats if c.get("dataset_id") == active_id] if active_id else []
    
    # Store list in session state for sidebar render access
    st.session_state["copilot_chats_list"] = chats_for_active_ds

    active_chat_id = st.session_state.get("active_chat_id")
    active_chat_ids = [c["id"] for c in chats_for_active_ds]
    
    # Check if we should spin a new chat session
    if (st.session_state.get("copilot_trigger_new_chat", False) or 
            not active_chat_id or 
            active_chat_id not in active_chat_ids) and active_id:
        
        new_id = str(uuid.uuid4())
        new_chat = {
            "id": new_id,
            "dataset_id": active_id,
            "title": "New Chat",
            "updated_at": datetime.now().strftime("%I:%M %p"),
            "messages": []
        }
        all_chats.insert(0, new_chat)
        _save_history_state(all_chats)
        st.session_state["active_chat_id"] = new_id
        st.session_state["copilot_trigger_new_chat"] = False
        chats_for_active_ds = [c for c in all_chats if c.get("dataset_id") == active_id]
        st.session_state["copilot_chats_list"] = chats_for_active_ds
        active_chat_id = new_id

    # Resolve active chat session messages
    current_chat = next((c for c in all_chats if c.get("id") == active_chat_id), None)
    messages_list = current_chat.get("messages", []) if current_chat else []

    # Handle quick query chip URL parameters
    try:
        raw_q = st.query_params.get("q")
    except AttributeError:
        try:
            raw_q = st.experimental_get_query_params().get("q", [None])[0]
        except Exception:
            raw_q = None

    # Intercept native state submission to prevent full page reloads
    native_q = st.session_state.get("copilot_search_query_state")
    if native_q:
        raw_q = native_q
        st.session_state["copilot_search_query_state"] = None

    typed_q = st.session_state.get("copilot_search_input_val")
    if typed_q:
        raw_q = typed_q

    is_dataset_cleaned = False
    if active_dataset:
        status_val = str(active_dataset.get("status") or "").upper()
        is_dataset_cleaned = status_val in ("CLEANED", "FEATURED", "READY")

    if raw_q and active_id and current_chat:
        try:
            st.query_params.clear()
        except AttributeError:
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
        
        # Enforce highly-performant single-turn replacing interaction by wiping previous turns
        messages_list.clear()
        
        messages_list.append({"role": "user", "content": raw_q})
        if current_chat.get("title") == "New Chat":
            current_chat["title"] = raw_q[:20] + ("..." if len(raw_q) > 20 else "")
        current_chat["updated_at"] = datetime.now().strftime("%I:%M %p")
        
        if True:
            if not is_dataset_cleaned:
                messages_list.append({
                    "role": "assistant",
                    "content": "Data preparation is required before analysis. Please clean the active dataset first in the Prepare Data page.",
                    "type": "text"
                })
            else:
                hybrid_res = get_hybrid_answer(raw_q, df)
                messages_list.append({
                    "role": "assistant",
                    "content": hybrid_res["content"],
                    "type": hybrid_res["type"],
                    **({"chart_data": hybrid_res["chart_data"]} if "chart_data" in hybrid_res else {}),
                    **({"insight": hybrid_res["insight"]} if "insight" in hybrid_res else {}),
                    **({"recommendation": hybrid_res["recommendation"]} if "recommendation" in hybrid_res else {})
                })
            _save_history_state(all_chats)
        st.rerun()

    # ══════════════════════════════════════════════════════════════
    #  UI LAYOUT SCENARIO RENDER
    # ══════════════════════════════════════════════════════════════
    
    # 1. Welcome Home Screen
    if True:
        if not datasets:
            st.info("📁 No datasets loaded. Please upload a dataset to begin.")
            if st.button("📤 Go to Upload Page", use_container_width=True):
                st.switch_page("pages/1_Upload_Data.py")
            st.stop()
            
        if not is_dataset_cleaned:
            st.warning("⚠️ **Data Preparation Required:** The active dataset has not been cleaned or prepared yet. Please go to the **Prepare Data** page to clean the dataset before using the Copilot.")
            if st.button("🧹 Go to Prepare Data Page", use_container_width=True):
                st.switch_page("pages/2_Prepare_Data.py")
            st.stop()
            
        # Global Button Redesign
        st.markdown("""
<style>
/* Premium Streamlit Buttons Redesign */
.stButton > button {
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.4) 0%, rgba(59, 130, 246, 0.4) 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 16px !important;
    color: #F8FAFC !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.6) 0%, rgba(59, 130, 246, 0.6) 100%) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    transform: scale(1.05) !important;
    box-shadow: 0 8px 25px rgba(168, 85, 247, 0.4), 0 0 15px rgba(59, 130, 246, 0.3) !important;
    color: #FFFFFF !important;
}
.stButton > button:active {
    transform: scale(0.98) !important;
}
</style>
""", unsafe_allow_html=True)
        
        # Compact Header and Hero Identity
        
        import base64
        import os
        logo_html = ""
        try:
            paths = ["static/ai-copilot-logo.png", "../static/ai-copilot-logo.png"]
            try: paths.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "ai-copilot-logo.png"))
            except: pass
            for p in paths:
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                        logo_html = f'<img class="hero-ai-logo-img" src="data:image/png;base64,{b64}" width="88" height="88" alt="Copilot" />'
                        break
        except:
            pass

        user_name = st.session_state.get("user", {}).get("name", "Avinash")
                
        css_payload = f"""
<style>
.premium-hero-wrapper {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    margin-bottom: 0px !important;
    padding-top: 10px;
}}
.hero-ai-logo-img {{
    display: block;
    margin-bottom: 0px !important;
    border-radius: 50%;
    border: none;
    animation: slowFloatOrb 4s ease-in-out infinite;
    box-shadow: 0 0 35px rgba(168, 85, 247, 0.45), 0 0 35px rgba(59, 130, 246, 0.45);
    filter: drop-shadow(0 0 15px rgba(168, 85, 247, 0.3)) drop-shadow(0 0 15px rgba(59, 130, 246, 0.3));
    background: transparent;
}}
@keyframes slowFloatOrb {{
    0% {{ transform: translateY(0px) scale(1); }}
    50% {{ transform: translateY(-6px) scale(1.02); }}
    100% {{ transform: translateY(0px) scale(1); }}
}}
.ai-glow-pulse {{
    animation: neonPulse 2.5s infinite ease-in-out;
    transform-origin: 50% 50%;
}}
@keyframes neonPulse {{
    0% {{ opacity: 0.8; transform: scale(0.98); }}
    50% {{ opacity: 1; transform: scale(1.02); }}
    100% {{ opacity: 0.8; transform: scale(0.98); }}
}}
.ai-particles-orbit {{
    animation: orbitSpin 20s linear infinite;
    transform-origin: 50px 50px;
}}
.ai-particles-outer {{
    animation: orbitSpinOuter 30s linear infinite;
    transform-origin: 50px 50px;
}}
@keyframes orbitSpin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}
@keyframes orbitSpinOuter {{
    0% {{ transform: rotate(360deg); }}
    100% {{ transform: rotate(0deg); }}
}}
.hero-welcome-text {{
    font-size: 42px !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    margin: 0 0 10px 0 !important;
    line-height: 1.2;
    letter-spacing: -1px !important;
}}
.hero-gradient-name {{
    color: #A855F7;
    filter: drop-shadow(0 2px 10px rgba(168, 85, 247, 0.3));
}}
.hero-subtitle {{
    font-size: 1.1rem !important;
    font-weight: 400;
    color: #94A3B8;
    margin: 0 !important;
}}

/* Centering structural layout */
div[data-testid="stVerticalBlock"]:has(#hero-unified-wrapper) {{
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    max-width: 1100px !important;
    width: 100% !important;
    margin: 0 auto !important;
    min-height: 85vh !important;
    gap: 0 !important;
}}
div[data-testid="stVerticalBlock"]:has(#hero-unified-wrapper) > div[data-testid="element-container"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

/* Make the form container completely invisible and structure-less */
div[data-testid="stForm"]:has(#custom-search-container) {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    height: 60px !important;
    display: flex !important;
    justify-content: center !important;
}}

/* Style the horizontal block inside as the Pill */
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stHorizontalBlock"] {{
    border: 0.5px solid rgba(168, 85, 247, 0.40) !important;
    border-radius: 9999px !important;
    padding: 0 8px !important;
    height: 60px !important;
    background: rgba(30, 30, 40, 0.35) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    box-shadow: inset 0 1px 3px rgba(255, 255, 255, 0.05) !important;
    transition: all 0.3s ease !important;
    display: flex !important;
    flex-wrap: nowrap !important;
    width: 720px !important;
    max-width: 90% !important;
    gap: 10px !important;
    align-items: center !important;
    margin: 0 auto !important;
    box-sizing: border-box !important;
    transform: translateX(15px) !important;
}}

div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stHorizontalBlock"]:hover,
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stHorizontalBlock"]:focus-within {{
    border-color: rgba(168, 85, 247, 0.6) !important;
    box-shadow: 0 0 20px rgba(168, 85, 247, 0.25), inset 0 1px 3px rgba(255, 255, 255, 0.05) !important;
    background: rgba(30, 30, 40, 0.45) !important;
}}

div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {{
    flex: 1 1 0% !important;
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {{
    flex: 0 0 48px !important;
    width: 48px !important;
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stVerticalBlock"] {{
    gap: 0px !important;
}}

/* Row 1 text input overrides to remove margins */
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] {{
    margin-bottom: 0 !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] *,
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] div[data-baseweb="base-input"] {{
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    outline: none !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] *::before,
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] *::after {{
    display: none !important;
    content: none !important;
    background: transparent !important;
    border: none !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] input {{
    background-color: transparent !important;
    color: #F8FAFC !important;
    font-size: 1.05rem !important;
    padding: 12px 0 12px 48px !important;
    height: 48px !important;
    line-height: 1.5 !important;
    box-shadow: none !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stTextInput"] input::placeholder {{
    color: #9CA3AF !important;
    opacity: 0.7 !important;
    font-weight: 400 !important;
    font-size: 1.05rem !important;
}}

/* Icons and buttons */
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stFormSubmitButton"] {{
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
    width: 48px !important;
    height: 48px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stFormSubmitButton"] button {{
    background: linear-gradient(135deg, #7C3AED, #5B21B6) !important;
    border-radius: 50% !important;
    height: 48px !important;
    width: 48px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: none !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stFormSubmitButton"] button p {{
    font-size: 20px !important;
    margin: 0 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    line-height: 1 !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stFormSubmitButton"] button:hover {{
    background: linear-gradient(135deg, #8B5CF6, #6D28D9) !important;
    transform: scale(1.05) !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.30) !important;
}}
div[data-testid="stForm"]:has(#custom-search-container) div[data-testid="stFormSubmitButton"] button:active {{
    transform: scale(0.95) !important;
}}

/* Suggestion Chips Styling */
div[data-testid="stVerticalBlock"]:has(#chip-container-marker) {{
    display: flex !important;
    flex-wrap: wrap !important;
    flex-direction: row !important;
    gap: 12px 16px !important;
    justify-content: center !important;
    max-width: 900px !important;
    margin: 0 auto !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    transform: translateY(-20px) !important;
}}
div[data-testid="stVerticalBlock"]:has(#chip-container-marker) > div {{
    width: auto !important;
    flex: 0 0 auto !important;
    margin: 0 !important;
    padding: 0 !important;
}}
#chip-container-marker {{
    display: none !important;
}}
div[data-testid="stVerticalBlock"]:has(#chip-container-marker) button {{
    background: rgba(18, 20, 32, 0.6) !important;
    border: 1px solid rgba(168, 85, 247, 0.4) !important;
    border-radius: 999px !important;
    color: #E2E8F0 !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    font-family: 'Inter', sans-serif !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    transition: all 0.3s ease !important;
    box-shadow: none !important;
    min-height: 36px !important;
    height: auto !important;
    width: auto !important;
    cursor: pointer !important;
}}
div[data-testid="stVerticalBlock"]:has(#chip-container-marker) button p {{
    margin: 0 !important;
    font-size: 13.5px !important;
}}
div[data-testid="stVerticalBlock"]:has(#chip-container-marker) button:hover {{
    background: rgba(167, 139, 250, 0.15) !important;
    border-color: rgba(168, 85, 247, 0.8) !important;
    transform: scale(1.03) !important;
    box-shadow: 0 0 15px rgba(168, 85, 247, 0.5) !important;
    color: #FFFFFF !important;
}}
div[data-testid="stVerticalBlock"]:has(#chip-container-marker) button:active {{
    transform: scale(0.98) !important;
}}
</style>
"""
        st.markdown(css_payload, unsafe_allow_html=True)
        
        # Define highly performant layout callbacks to prevent UI flashing
        def _handle_back_click():
            if messages_list is not None:
                messages_list.clear() # Wipe the current AI answer natively before render
                _save_history_state(all_chats)
            # Wipe search query registers so the engine doesn't immediately re-trigger 
            st.session_state["copilot_search_query_state"] = None
            if "copilot_search_input_val" in st.session_state:
                st.session_state.pop("copilot_search_input_val")
                
        def _handle_chip_click(suggestion):
            st.session_state["copilot_search_query_state"] = suggestion
            
        main_hero = st.container()
        with main_hero:
            st.markdown('''
            <style>
            .back-to-dashboard-hook {
                position: absolute;
                top: -30px;
                left: 0;
                z-index: 100;
            }
            .back-to-dashboard-hook [data-testid="stButton"] button {
                background: rgba(18, 20, 32, 0.4) !important;
                border: 1px solid rgba(168, 85, 247, 0.4) !important;
                padding: 4px 14px !important;
                color: #E2E8F0 !important;
                font-size: 0.85rem !important;
                border-radius: 8px !important;
                transition: all 0.2s ease !important;
                box-shadow: none !important;
                width: auto !important;
            }
            .back-to-dashboard-hook [data-testid="stButton"] button:hover {
                background: rgba(168, 85, 247, 0.15) !important;
                border-color: rgba(168, 85, 247, 0.8) !important;
                color: #ffffff !important;
            }
            </style>
            ''', unsafe_allow_html=True)
            
            if messages_list:
                st.markdown('<div class="back-to-dashboard-hook">', unsafe_allow_html=True)
                st.button("← Back", key="btn_back_to_dashboard", on_click=_handle_back_click)
                st.markdown('</div>', unsafe_allow_html=True)
                
            if not messages_list:
                landing_zone = st.empty()
                with landing_zone.container():
                    st.markdown('<div id="hero-unified-wrapper"></div>', unsafe_allow_html=True)
                    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0px; transform: translateY(50px);">
    <div style="margin-bottom: 32px; width: 100%; display: flex; justify-content: center;">{logo_html}</div>
    
    <h1 class="hero-welcome-text" style="display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 8px; margin: 0 0 12px 0 !important; padding: 0 !important;">
    <span>Welcome back!</span>
    </h1>
    
    <p class="hero-subtitle" style="margin: 0 0 28px 0 !important; padding: 0 !important;">Which business insight do you want to explore today?</p>
    </div>
    """, unsafe_allow_html=True)
                
                    with st.form("chat_input_form", clear_on_submit=True, border=False):
                        st.markdown('<div id="custom-search-container"></div>', unsafe_allow_html=True)
                        col_input, col_submit = st.columns([0.92, 0.08])
                        with col_input:
                            st.text_input("search", placeholder="Ask anything about your business data...", label_visibility="collapsed", key="copilot_search_input_val")
                        with col_submit:
                            st.markdown('<div class="circ-send-btn">', unsafe_allow_html=True)
                            st.form_submit_button("↑", help="Send message")
                            st.markdown('</div>', unsafe_allow_html=True)
        
                    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
                    chip_suggestions = [
                        "💰 Total Revenue",
                        "📈 Monthly Sales Trend",
                        "📦 Top Products",
                        "🌍 Best Region",
                        "👥 Top Customers",
                        "🤖 Revenue Forecast"
                    ]
                    
                    chip_box = st.container()
                    with chip_box:
                        st.markdown('<div id="chip-container-marker"></div>', unsafe_allow_html=True)
                        for i, s in enumerate(chip_suggestions):
                            st.button(s, key=f"chip_sugg_{i}", on_click=_handle_chip_click, args=(s,))
            else:
                # If there are active messages, ensure the landing zone is completely wiped from the DOM.
                pass
        
        # INLINE RESPONSE PANEL
        if messages_list:
            last_msg = messages_list[-1]
            if last_msg["role"] == "assistant":
                query_text = messages_list[-2]["content"].strip() if len(messages_list) > 1 else "Business Query"
                title = query_text.capitalize() if len(query_text) < 40 else "AI Business Analysis"
                
                # Active Module Context Tracking
                source_mod = "KPI Dashboard"
                q_lower = query_text.lower()
                if "forecast" in q_lower or "predict" in q_lower: source_mod = "Forecasting Module"
                elif "anomaly" in q_lower or "outlier" in q_lower: source_mod = "Anomaly Detection"
                elif "segment" in q_lower or "customer" in q_lower: source_mod = "Customer Intelligence"
                elif "quality" in q_lower or "missing" in q_lower: source_mod = "Data Preparation"

                rendered_content = last_msg.get('content', '')
                
                st.markdown(f"""
<style>
/* Provide premium typography formatting specifically for this AI response content payload */
.fabric-card-body h3 {{
    font-size: 1.15rem !important;
    font-weight: 500 !important;
    color: #94A3B8 !important;
    margin: 0 0 15px 0 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.fabric-card-body h1 {{
    font-size: 3.5rem !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    margin: 0 0 35px 0 !important;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #F8FAFC 0%, #A855F7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.fabric-card-body p {{
    margin-bottom: 25px !important;
    line-height: 1.8 !important;
    font-size: 1.05rem !important;
}}
.fabric-card-body strong {{
    color: #E2E8F0 !important;
    font-weight: 600 !important;
}}
.fabric-card-body ul {{
    text-align: left !important;
    margin-bottom: 25px !important;
}}
.fabric-card-body li {{
    margin-bottom: 8px !important;
}}
</style>
</style>
<div style="max-width: 100%; margin: 0 auto; display: flex; flex-direction: column; width: 100%;">
    <div style="align-self: flex-end; background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%); color: #fff; padding: 14px 22px; border-radius: 20px 20px 4px 20px; max-width: 75%; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.25); font-size: 1.05rem; font-weight: 500;">
        {query_text}
    </div>
</div>
""", unsafe_allow_html=True)

                m_type = last_msg.get("type", "text")
                
                # Dynamic layout: Side-by-Side for Charts, Full-width for Text
                if m_type == "chart":
                    col_txt, col_fig = st.columns([1, 1], gap="medium")
                    
                    with col_txt:
                        st.markdown(f"""
                        <div class="fabric-insight-card" style="padding: 24px; text-align: left; height: 100%;">
                            <div class="fabric-card-body" style="text-align: left;">
                                {rendered_content}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_fig:
                        c_data = last_msg.get("chart_data", {})
                        c_type = c_data.get("type", "line")
                        fig = go.Figure()
                        
                        if c_type == "bar":
                            fig.add_trace(go.Bar(
                                x=c_data.get("x", []), y=c_data.get("y", []),
                                marker_color="#A5B4FC"
                            ))
                        else:
                            fig.add_trace(go.Scatter(
                                x=c_data.get("x", []), y=c_data.get("y", []),
                                mode="lines+markers", line=dict(color="#A5B4FC", width=3),
                                marker=dict(size=6, color="#FFFFFF")
                            ))
                            
                        theme = st.session_state.get("theme", "dark")
                        txt_color = "#334155" if theme == "light" else "#94A3B8"
                        grid_color = "rgba(0,0,0,0.08)" if theme == "light" else "rgba(255,255,255,0.05)"
                        
                        fig.update_layout(
                            title=c_data.get("title", "Insight Chart"), height=350,
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font={"color": txt_color},
                            margin={"t": 35, "l": 15, "r": 15, "b": 10},
                            xaxis={"showgrid": True, "gridcolor": grid_color},
                            yaxis={"showgrid": True, "gridcolor": grid_color}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div style="max-width: 900px; margin: 0 auto; width: 100%;">
                        <div class="fabric-insight-card" style="padding: 30px; text-align: left;">
                            <div class="fabric-card-body" style="text-align: left;">
                                {rendered_content}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Chat log mode removed per requirements. Inline response pane answers everything.

    # ══════════════════════════════════════════════════════════════
    #  FAISS SEARCH INDEX BUILDING GUARD
    # ══════════════════════════════════════════════════════════════
    if active_id:
        if not st.session_state.get(_chat_key("indexed")):
            try:
                api_client.index_dataset(active_id)
                st.session_state[_chat_key("indexed")] = True
            except Exception:
                pass

        # Chat input is removed as requested by the user
        pass

