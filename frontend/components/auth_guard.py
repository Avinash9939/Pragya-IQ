import streamlit as st
from frontend.utils.session import is_logged_in, get_current_user


def require_login() -> None:
    """
    Enforces active authenticated session guard at the page level.
    Why: Prevents direct URL accesses to protected dashboards when unauthenticated.
    """
    if not is_logged_in():
        st.switch_page("streamlit_app.py")
        st.stop()


def require_role(*allowed_roles: str) -> None:
    """
    Client-side Role-Based Access Control (RBAC) component helper.
    Why: Improves user experience by early-hiding actions from unauthorized roles.
    """
    # Force authentication check first
    require_login()
    
    user = get_current_user()
    if user is None:
        st.error("❌ Failed to resolve user profile details. Please log in again.")
        st.stop()
        
    user_role = user.get("role", "")
    if user_role not in allowed_roles:
        st.error(
            f"❌ Unauthorized access. Your current role ('{user_role}') "
            f"does not have permission to view this view."
        )
        st.info(f"Allowed roles for this action: {', '.join(allowed_roles)}")
        st.stop()
