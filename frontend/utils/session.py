import streamlit as st


def is_logged_in() -> bool:
    """
    Checks if there is an active authenticated user session.
    Why: Dictates navigation logic and sidebar rendering options.
    """
    return "access_token" in st.session_state and "user" in st.session_state


def get_current_user() -> dict | None:
    """
    Retrieves caching details of the logged in user profile.
    Why: Used for client-side ownership checking and UI greeting.
    """
    return st.session_state.get("user")


def logout() -> None:
    """
    Clears all auth credentials and cached tokens from session state.
    Why: Safely ends the application session.
    """
    st.session_state.pop("access_token", None)
    st.session_state.pop("user", None)
    # Also drop cached files or temporary parameters to prevent state leakages
    st.session_state.pop("active_dataset_id", None)
