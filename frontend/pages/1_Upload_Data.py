import os
import streamlit as st

from frontend.components.auth_guard import require_login
from frontend.components.sidebar import render_sidebar

# Enforce authentication guard early
require_login()



# Render global unified sidebar Immediately


import pandas as pd
from datetime import datetime
from frontend.services import api_client

# Load user context
user = st.session_state.get("user", {})
user_id = user.get("id", 1)
email = user.get("email", "avinash5015@gmail.com")

# Load existing datasets list
try:
    datasets = api_client.list_datasets(force_refresh=True)
except Exception as e:
    datasets = []

# Fetch active dataset ID
active_id = st.session_state.get("active_dataset_id")
if not active_id and datasets:
    active_id = datasets[0]["id"]
    st.session_state["active_dataset_id"] = active_id

from frontend.utils.dataset_cache import calculate_dataset_metrics

# Pre-calculate active dataset metrics
active_dataset = None
active_metrics = {"rows": 0, "cols": 0, "missing": 0, "duplicates": 0, "quality": 96, "status": "Validated & Ready"}

for d in datasets:
    if d["id"] == active_id:
        active_dataset = d
        m = calculate_dataset_metrics(user_id, d["id"], d["filename"])
        active_metrics = m
        if d["status"] in ("CLEANED", "FEATURED", "READY"):
            active_metrics["status"] = "Cleaned & Ready"
        elif d["status"] == "UPLOADED" and m["missing"] == 0:
            active_metrics["status"] = "Validated & Ready"
        elif d["status"] == "FEATURE_ENGINEERED":
            active_metrics["status"] = "Ready (ML Models)"
        break



# Inject custom layout styles (hover states, animations, larger upload box)
st.markdown("""
<style>
    .dataset-upload-card-new {
        height: auto;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 32px;
        background: rgba(15, 8, 29, 0.45);
        border: 2px dashed rgba(168, 85, 247, 0.3);
        border-radius: 12px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .dataset-upload-card-new:hover {
        border-color: rgba(168, 85, 247, 0.8) !important;
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.4) !important;
        transform: translateY(-2px);
    }
    .supported-formats-card-new {
        height: auto;
        min-height: 220px;
        background: rgba(15, 8, 29, 0.45);
        border: 1px solid rgba(168, 85, 247, 0.15);
        border-radius: 12px;
        padding: 24px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    @keyframes float-animation {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
        100% { transform: translateY(0px); }
    }
    .dataset-upload-card-new:hover .upload-logo-svg {
        animation: float-animation 2s ease-in-out infinite;
    }
</style>
""", unsafe_allow_html=True)

# 2. Main Page Header
st.markdown("""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom: 24px;">
        <div style="width:48px; height:48px; background:rgba(109, 40, 217, 0.2); border: 1px solid rgba(168, 85, 247, 0.3); border-radius:10px; display:flex; align-items:center; justify-content:center;">
            <svg viewBox="0 0 24 24" width="28" height="28" stroke="#C084FC" stroke-width="2" fill="none"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
        </div>
        <div>
            <h1 style="color:#FFF; font-size:1.85rem; font-weight:700; margin:0; line-height:1.2;">Dataset Upload & Management</h1>
            <p style="color:#9CA3AF; font-size:0.85rem; margin:2px 0 0 0;">Upload, manage and prepare your business datasets for AI-powered insights.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# 3. Main Area: Upload Box & Supported Formats Page Components
col_upload_left, col_upload_right = st.columns([6.8, 3.2])

with col_upload_left:
    st.markdown("""
        <div class="dataset-upload-card-new">
            <div class="upload-logo-svg" style="width:60px; height:60px; background:rgba(109, 40, 217, 0.1); border-radius:50%; display:flex; align-items:center; justify-content:center; margin-bottom:16px; border: 1px dashed rgba(168, 85, 247, 0.4);">
                <svg viewBox="0 0 24 24" width="32" height="32" stroke="#C084FC" stroke-width="2" fill="none"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
            </div>
            <div style="font-size:0.95rem; font-weight:700; color:#FFF; margin-bottom:4px;">Drag & Drop your file here</div>
            <div style="font-size:0.7rem; color:#8E8EA8; margin-bottom:12px;">or drag and drop your file into the drag-drop selector below</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Real file uploader from Streamlit
    MAX_FILE_SIZE_MB = 10
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    uploaded_file = st.file_uploader(
        "Choose a dataset file",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
        help="Supported formats: CSV, XLSX, XLS. Limit 10MB."
    )
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_size_bytes = len(file_bytes)
        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            st.error(f"❌ File too large! Exceeds maximum limit of {MAX_FILE_SIZE_MB}MB.")
        else:
            # Show upload progress when a file is uploading
            progress_bar = st.progress(0, text="Initializing file upload stream...")
            import time
            for percent in range(25, 101, 25):
                time.sleep(0.05)
                progress_bar.progress(percent, text=f"Uploading dataset: {percent}%")
                
            if st.button("📤 Upload and Process Dataset", use_container_width=True, type="primary"):
                try:
                    progress_bar.progress(90, text="Saving and registering dataset metadata...")
                    result = api_client.upload_dataset(uploaded_file)
                    progress_bar.progress(100, text="Upload complete!")
                    st.success(f"🎉 Successfully uploaded **{result.get('filename')}**!")
                    st.session_state["active_dataset_id"] = result["id"]
                    if "api_cached_datasets" in st.session_state:
                        del st.session_state["api_cached_datasets"]
                    st.rerun()
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Error uploading dataset: {str(e)}")

with col_upload_right:
    st.markdown("""
        <div class="supported-formats-card-new">
            <div>
                <div style="border-bottom:1px solid rgba(168, 85, 247, 0.15); padding-bottom:10px; margin-bottom:18px;">
                    <span style="font-size:0.92rem; font-weight:700; color:#FFF; display:flex; align-items:center; gap:8px;">
                        <svg viewBox="0 0 24 24" width="14" height="14" stroke="#C084FC" stroke-width="2.5" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        Supported Formats
                    </span>
                </div>
                <!-- CSV -->
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
                    <div style="background:rgba(59, 130, 246, 0.15); color:#60A5FA; font-weight:bold; font-size:0.7rem; padding:4px 8px; border-radius:4px; border:1px solid rgba(59, 130, 246, 0.3);">CSV</div>
                    <div>
                        <div style="font-size:0.8rem; font-weight:700; color:#FFF;">CSV</div>
                        <div style="font-size:0.65rem; color:#8E8EA8;">Comma-separated values (.csv)</div>
                    </div>
                </div>
                <!-- Excel -->
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
                    <div style="background:rgba(16, 185, 129, 0.15); color:#34D399; font-weight:bold; font-size:0.7rem; padding:4px 8px; border-radius:4px; border:1px solid rgba(16, 185, 129, 0.3);">XLS</div>
                    <div>
                        <div style="font-size:0.8rem; font-weight:700; color:#FFF;">Excel Spreadsheets</div>
                        <div style="font-size:0.65rem; color:#8E8EA8;">Excel workbooks (.xlsx, .xls)</div>
                    </div>
                </div>
                <!-- Google Sheets -->
                <div style="display:flex; align-items:center; gap:12px; opacity:0.6;">
                    <div style="background:rgba(245, 158, 11, 0.15); color:#F59E0B; font-weight:bold; font-size:0.7rem; padding:4px 8px; border-radius:4px; border:1px solid rgba(245, 158, 11, 0.3);">GSH</div>
                    <div>
                        <div style="font-size:0.8rem; font-weight:700; color:#FFF;">Google Sheets</div>
                        <div style="font-size:0.65rem; color:#8E8EA8;">Cloud sheets integration (coming soon)</div>
                    </div>
                </div>
            </div>
            <div style="font-size:0.68rem; color:#9CA3AF; border-top: 1px solid rgba(255,255,255,0.05); padding-top:12px;">
                🛡️ All uploads are encrypted and processed locally. Limit: 10MB per file.
            </div>
        </div>
    """, unsafe_allow_html=True)

st.write("")


# 4. Your Datasets Table List Section
st.markdown("""
    <div class="card-header-row" style="border:none; margin-bottom:8px;">
        <span style="font-size:1.0rem; font-weight:700; color:#FFF; display:flex; align-items:center; gap:8px;">
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="#C084FC" stroke-width="2" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/></svg>
            Your Datasets
        </span>
    </div>
""", unsafe_allow_html=True)



# Custom Table Headers
st.markdown("""
    <div style="display:flex; align-items:center; padding:8px 10px; background:rgba(109, 40, 217, 0.1); border:1px solid rgba(168, 85, 247, 0.15); border-radius:6px; margin-bottom:8px; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">
        <div style="flex: 4;">Dataset</div>
        <div style="flex: 1.5; text-align:center;">Rows</div>
        <div style="flex: 1.5; text-align:center;">Cols</div>
        <div style="flex: 2; text-align:center;">Quality Score</div>
        <div style="flex: 2; text-align:center;">Status</div>
        <div style="flex: 2.5; text-align:center;">Uploaded At</div>
        <div style="flex: 1.5; text-align:center;">Action</div>
    </div>
""", unsafe_allow_html=True)

if not datasets:
    st.info("No datasets uploaded yet. Choose a file above to upload!")
else:

        
    for index, d in enumerate(datasets):
        metrics = calculate_dataset_metrics(user_id, d["id"], d["filename"])
        
        # Render each row inside styled elements
        col_t_row = st.columns([4, 1.5, 1.5, 2, 2.5, 2.5, 1.5])
        
        formatted_date = pd.to_datetime(d["uploaded_at"]).strftime("%d %b %Y, %I:%M %p")
        status_label = "Validated"
        status_color = "#34D399" # green dot
        if d["status"] in ("CLEANED", "FEATURED", "READY"):
            status_label = "Cleaned"
            status_color = "#C084FC"
        elif d["status"] == "FEATURE_ENGINEERED":
            status_label = "Ready"
            status_color = "#60A5FA"
        elif metrics["missing"] > 0:
            status_label = "Needs Cleaning"
            status_color = "#FBBF24" # yellow dot
            
        is_active_row = (d["id"] == active_id)
        active_border_color = "rgba(168, 85, 247, 0.45)" if is_active_row else "rgba(168, 85, 247, 0.08)"
        active_bg = "rgba(109, 40, 217, 0.08)" if is_active_row else "rgba(15, 8, 29, 0.3)"
        
        # Inject styled background wrappers around the columns using st.html / markdown hacks or direct styles
        with col_t_row[0]:
            # File logo and filename ID
            logo_svg = '<svg viewBox="0 0 24 24" width="14" height="14" stroke="#34d399" stroke-width="2.5" fill="none" style="vertical-align:middle; margin-right:4px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
            if d["filename"].endswith(".csv"):
                logo_svg = '<svg viewBox="0 0 24 24" width="14" height="14" stroke="#60a5fa" stroke-width="2.5" fill="none" style="vertical-align:middle; margin-right:4px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
            
            st.markdown(f"""
                <div style="font-size:0.75rem; font-weight:600; padding:6px 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                    {logo_svg} {d['filename']}
                    <span style="font-size:0.6rem; color:#8E8EA8; font-weight: normal; margin-left:6px;">ID: {d['id']}</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col_t_row[1]:
            st.markdown(f'<div style="text-align:center; font-size:0.75rem; padding:6px 0;">{metrics["rows"]:,}</div>', unsafe_allow_html=True)
            
        with col_t_row[2]:
            st.markdown(f'<div style="text-align:center; font-size:0.75rem; padding:6px 0;">{metrics["cols"]}</div>', unsafe_allow_html=True)
            
        with col_t_row[3]:
            st.markdown(f"""
                <div style="text-align:center; font-size:0.75rem; padding:6px 0;">
                    <span style="vertical-align:middle; margin-right:4px;">{metrics['quality']}%</span>
                    <div class="progress-bar-container" style="width:40px;"><div class="progress-bar-fill purple" style="width: {metrics['quality']}%"></div></div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_t_row[4]:
            st.markdown(f"""
                <div style="text-align:center; font-size:0.75rem; padding:6px 0;">
                    <span style="display:inline-block; width:5px; height:5px; background:{status_color}; border-radius:50%; margin-right:4px; box-shadow:0 0 4px {status_color};"></span>
                    {status_label}
                </div>
            """, unsafe_allow_html=True)
            
        with col_t_row[5]:
            st.markdown(f'<div class="dataset-table-date" style="text-align:center; font-size:0.7rem; padding:6px 0;">{formatted_date}</div>', unsafe_allow_html=True)
            
        with col_t_row[6]:
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                # View/Select context button
                if st.button("👁️", key=f"select_ds_{d['id']}", help="Set as active dataset context"):
                    st.session_state["active_dataset_id"] = d["id"]
                    st.rerun()
            with act_col2:
                # Delete button
                if st.button("🗑️", key=f"delete_ds_{d['id']}", help="Delete dataset"):
                    try:
                        api_client.delete_dataset(d["id"])
                        if st.session_state.get("active_dataset_id") == d["id"]:
                            st.session_state.pop("active_dataset_id", None)
                        if "api_cached_datasets" in st.session_state:
                            del st.session_state["api_cached_datasets"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # Inject background boundary color container using CSS selection
        st.markdown(f"""
            <style>
                div[data-testid="column"]:nth-of-type(odd) {{
                    /* custom padding alignments */
                }}
            </style>
        """, unsafe_allow_html=True)
