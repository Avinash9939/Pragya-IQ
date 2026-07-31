import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from frontend.components.auth_guard import require_role

def show_page():
    # Enforce Admin Access Check
    require_role("admin", "analyst")

    # Custom styles injection for theme integration
    css_style = """
    <style>
        /* Card Styles */
        .metric-card {
            background: rgba(18, 26, 54, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            text-align: center;
        }
        .metric-title {
            color: #94A3B8;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        .metric-value {
            color: #FFFFFF;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .metric-subtitle {
            color: #C084FC;
            font-size: 13px;
            font-weight: 600;
            margin-top: 4px;
        }
    </style>
    """
    st.markdown(css_style, unsafe_allow_html=True)

    # Page header
    st.markdown("<h1 style='color: #FFFFFF; margin-bottom: 0px;'>🛡️ Enterprise Admin Dashboard</h1>", unsafe_allow_html=True)
    st.caption("Central administrative suite for systems observability, users control, and model governance configurations.")
    st.markdown("<br>", unsafe_allow_html=True)

    # Persistent Mock Data initialization in streamlit session state
    if "admin_users" not in st.session_state:
        st.session_state["admin_users"] = pd.DataFrame([
            {"id": 1, "Name": "Alice Johnson", "Email": "alice@netgentry.io", "Role": "Admin", "Status": "Active"},
            {"id": 2, "Name": "Bob Smith", "Email": "bob@netgentry.io", "Role": "Viewer", "Status": "Active"},
            {"id": 3, "Name": "Charlie Brown", "Email": "charlie@netgentry.io", "Role": "Editor", "Status": "Suspended"},
            {"id": 4, "Name": "Diana Prince", "Email": "diana@netgentry.io", "Role": "Viewer", "Status": "Active"}
        ])

    if "admin_datasets" not in st.session_state:
        st.session_state["admin_datasets"] = pd.DataFrame([
            {"id": 1, "Dataset Name": "SuperStore_Sales_2026.csv", "Owner": "Alice Johnson", "Rows": 9994, "Upload Date": "2026-07-15"},
            {"id": 2, "Dataset Name": "Customer_Churn_Data.xlsx", "Owner": "Bob Smith", "Rows": 5000, "Upload Date": "2026-07-16"},
            {"id": 3, "Dataset Name": "Product_Inventory_List.csv", "Owner": "Charlie Brown", "Rows": 320, "Upload Date": "2026-07-14"}
        ])

    if "admin_ai_settings" not in st.session_state:
        st.session_state["admin_ai_settings"] = {
            "model": "Gemini 1.5 Pro",
            "temperature": 0.70,
            "max_tokens": 2048
        }

    # ══════════════════════════════════════════════════════════════
    #  SECTIONS ROUTER - TABS LAYOUT
    # ══════════════════════════════════════════════════════════════
    t_dash, t_users, t_sets, t_ai = st.tabs([
        "📊 Observability Dashboard",
        "👥 User Management",
        "💾 Dataset Governance",
        "⚙️ AI Model Settings"
    ])

    # ──────────────────────────────────────────────────────────────
    #  SECTION 1: DASHBOARD
    # ──────────────────────────────────────────────────────────────
    with t_dash:
        st.markdown("<h3 style='margin-bottom: 20px;'>📊 System Observability</h3>", unsafe_allow_html=True)
        
        # Calculate counts
        user_count = len(st.session_state["admin_users"])
        dataset_count = len(st.session_state["admin_datasets"])
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">Total Users</div>
                    <div class="metric-value">{user_count}</div>
                    <div class="metric-subtitle">Active Accounts</div>
                </div>
            ''', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">Total Datasets</div>
                    <div class="metric-value">{dataset_count}</div>
                    <div class="metric-subtitle">Database Cache</div>
                </div>
            ''', unsafe_allow_html=True)
        with c3:
            st.markdown('''
                <div class="metric-card">
                    <div class="metric-title">AI Requests</div>
                    <div class="metric-value">1,482</div>
                    <div class="metric-subtitle">+12.4% this week</div>
                </div>
            ''', unsafe_allow_html=True)
        with c4:
            st.markdown('''
                <div class="metric-card">
                    <div class="metric-title">System Status</div>
                    <div class="metric-value" style="color: #10B981;">Operational</div>
                    <div class="metric-subtitle">All Services Live</div>
                </div>
            ''', unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### Observability Logs & System Latency")
        
        col_l1, col_l2 = st.columns([2, 1])
        with col_l1:
            time_index = pd.date_range(start="2026-07-17 00:00", periods=24, freq="h")
            mock_latency = 120 + 40 * np.sin(np.linspace(0, 3 * np.pi, 24)) + np.random.randint(-15, 15, 24)
            chart_df = pd.DataFrame({"Latency (ms)": mock_latency}, index=time_index)
            st.line_chart(chart_df, height=220)
        with col_l2:
            st.markdown("**Core Services Health**")
            st.write("🟢 REST API Interface")
            st.write("🟢 Vector Search Pipeline")
            st.write("🟢 ML Execution Node")
            st.write("🟢 Database Cluster")

    # ──────────────────────────────────────────────────────────────
    #  SECTION 2: USER MANAGEMENT
    # ──────────────────────────────────────────────────────────────
    with t_users:
        st.markdown("<h3 style='margin-bottom: 20px;'>👥 User Management Control</h3>", unsafe_allow_html=True)
        
        users_df = st.session_state["admin_users"]
        st.dataframe(
            users_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("User Name", width="medium"),
                "Email": st.column_config.TextColumn("Email Address", width="large"),
                "Role": st.column_config.TextColumn("Access Role", width="small"),
                "Status": st.column_config.TextColumn("Account Status", width="small")
            }
        )
        
        st.markdown("<hr style='border: 0.5px solid rgba(255, 255, 255, 0.08);'>", unsafe_allow_html=True)
        
        col_u_act, col_u_form = st.columns([1, 2])
        with col_u_act:
            st.markdown("#### Actions")
            selected_user = st.selectbox(
                "Select User to edit/delete",
                options=users_df["Email"].tolist(),
                key="user_select_opt"
            )
            sub_c1, sub_c2 = st.columns(2)
            with sub_c1:
                btn_edit_trigger = st.button("✏️ Edit User", type="secondary", use_container_width=True)
            with sub_c2:
                btn_delete_trigger = st.button("🗑️ Delete User", type="primary", use_container_width=True)
                
            if btn_delete_trigger:
                st.session_state["admin_users"] = users_df[users_df["Email"] != selected_user]
                st.toast(f"🗑️ User '{selected_user}' has been deleted successfully.")
                st.rerun()
                
        with col_u_form:
            if btn_edit_trigger or st.session_state.get("active_edit_mode") == selected_user:
                st.session_state["active_edit_mode"] = selected_user
                user_data = users_df[users_df["Email"] == selected_user].iloc[0]
                
                st.markdown(f"**Edit Account: {selected_user}**")
                with st.form("edit_user_form", clear_on_submit=True):
                    new_name = st.text_input("Name", value=user_data["Name"])
                    new_role = st.selectbox("Role", options=["Admin", "Editor", "Viewer"], index=["Admin", "Editor", "Viewer"].index(user_data["Role"]))
                    new_status = st.selectbox("Status", options=["Active", "Suspended"], index=["Active", "Suspended"].index(user_data["Status"]))
                    
                    submitted = st.form_submit_button("💾 Save Account Changes")
                    if submitted:
                        df_copy = users_df.copy()
                        idx = df_copy[df_copy["Email"] == selected_user].index[0]
                        df_copy.at[idx, "Name"] = new_name
                        df_copy.at[idx, "Role"] = new_role
                        df_copy.at[idx, "Status"] = new_status
                        st.session_state["admin_users"] = df_copy
                        st.session_state.pop("active_edit_mode", None)
                        st.toast(f"✅ User profiles updated for '{selected_user}'!")
                        st.rerun()
            else:
                st.info("💡 Select a user from the dropdown and click 'Edit User' to modify their database profile fields.")

    # ──────────────────────────────────────────────────────────────
    #  SECTION 3: DATASET MANAGEMENT
    # ──────────────────────────────────────────────────────────────
    with t_sets:
        st.markdown("<h3 style='margin-bottom: 20px;'>💾 Dataset Governance Console</h3>", unsafe_allow_html=True)
        
        datasets_df = st.session_state["admin_datasets"]
        st.dataframe(
            datasets_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "Dataset Name": st.column_config.TextColumn("Dataset Filename", width="large"),
                "Owner": st.column_config.TextColumn("Uploader", width="medium"),
                "Rows": st.column_config.NumberColumn("Total Records", width="small"),
                "Upload Date": st.column_config.TextColumn("Created Date", width="small")
            }
        )
        
        st.markdown("<hr style='border: 0.5px solid rgba(255, 255, 255, 0.08);'>", unsafe_allow_html=True)
        
        col_d_act, col_d_view = st.columns([1, 2])
        with col_d_act:
            st.markdown("#### Dataset Control")
            selected_ds_name = st.selectbox(
                "Select dataset to govern",
                options=datasets_df["Dataset Name"].tolist(),
                key="governance_dataset_select"
            )
            ds_c1, ds_c2 = st.columns(2)
            with ds_c1:
                btn_prev_ds = st.button("🔍 Preview Columns", use_container_width=True)
            with ds_c2:
                btn_del_ds = st.button("🗑️ Delete Dataset", type="primary", use_container_width=True)
                
            if btn_del_ds:
                st.session_state["admin_datasets"] = datasets_df[datasets_df["Dataset Name"] != selected_ds_name]
                st.toast(f"🗑️ Dataset '{selected_ds_name}' deleted successfully.")
                st.rerun()
                
        with col_d_view:
            if btn_prev_ds:
                ds_info = datasets_df[datasets_df["Dataset Name"] == selected_ds_name].iloc[0]
                st.markdown(f"**Previewing schema of: `{selected_ds_name}`**")
                
                mock_cols = [
                    {"Column Name": "Transaction_ID", "Type": "Integer", "Sample Value": "10042"},
                    {"Column Name": "Order Date", "Type": "Date", "Sample Value": "2026-07-15"},
                    {"Column Name": "Customer_ID", "Type": "Integer", "Sample Value": "8833"},
                    {"Column Name": "Sales", "Type": "Float", "Sample Value": "429.50"},
                    {"Column Name": "Sales_outlier", "Type": "Boolean", "Sample Value": "False"}
                ]
                st.table(pd.DataFrame(mock_cols))
            else:
                st.info("💡 Select any dataset filename to inspect field schemas, column maps or perform soft deletions.")

    # ──────────────────────────────────────────────────────────────
    #  SECTION 4: AI SETTINGS
    # ──────────────────────────────────────────────────────────────
    with t_ai:
        st.markdown("<h3 style='margin-bottom: 20px;'>⚙️ AI Model & Inference Governance</h3>", unsafe_allow_html=True)
        
        settings = st.session_state["admin_ai_settings"]
        
        col_ai_l, col_ai_r = st.columns(2)
        with col_ai_l:
            current_model = st.selectbox(
                "Current AI Model",
                options=["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini 1.0 Ultra"],
                index=["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini 1.0 Ultra"].index(settings["model"]),
                help="Choose the model used for LLM Chat copilot and strategic recommendations generation."
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=float(settings["temperature"]),
                step=0.05,
                help="Controls creativity: higher values mean more creative but less predictable outcomes."
            )
            
        with col_ai_r:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=256,
                max_value=8192,
                value=int(settings["max_tokens"]),
                step=256,
                help="Maximum output sequence length limit generated by the model backend."
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        btn_save_ai = st.button("💾 Save Settings", type="primary")
        
        if btn_save_ai:
            st.session_state["admin_ai_settings"] = {
                "model": current_model,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            st.toast("✅ AI Model & Inference parameters saved and loaded into active services!")
