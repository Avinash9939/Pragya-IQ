import streamlit as st
from frontend.services import api_client
from frontend.utils.session import logout


def render_dataset_selector() -> int | None:
    """
    Renders a unified selectbox to choose the active dataset for analysis.
    Why: Share dataset scope across ML, details, and chat pages.
    """
    try:
        datasets = api_client.list_datasets()
    except api_client.ApiError as e:
        if e.status_code == 401:
            logout()
            st.error("🔒 Your session has expired. Please log in again.")
            st.rerun()
        else:
            st.warning(f"⚠️ Could not load datasets list: {e.message} (HTTP {e.status_code})")
        return None
    except Exception as e:
        st.warning(f"⚠️ Could not load datasets list: {str(e)}")
        return None

    if not datasets:
        st.info("ℹ️ No datasets yet — upload one first.")
        st.page_link("pages/1_Upload_Data.py", label="Go to Upload Page", icon="📤")
        st.session_state.pop("active_dataset_id", None)
        return None

    # Construct clean key mappings
    options = {d["id"]: f"📊 {d['filename']} (ID: {d['id']})" for d in datasets}
    
    # Resolve currently selected dataset
    active_id = st.session_state.get("active_dataset_id")
    if active_id not in options:
        active_id = list(options.keys())[0]
        st.session_state["active_dataset_id"] = active_id

    index = list(options.keys()).index(active_id)

    selected_id = st.sidebar.selectbox(
        "Active Dataset Context",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        index=index,
        help="Select the dataset context to run reports or chat with AI."
    )

    # Sync selection changes back into state and trigger rerun to refresh charts
    if selected_id != st.session_state.get("active_dataset_id"):
        st.session_state["active_dataset_id"] = selected_id
        st.rerun()

    return selected_id
