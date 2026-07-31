import streamlit as st


def empty_state(
    message: str,
    icon: str = "📂",
    action_label: str | None = None,
    action_page: str | None = None,
    action_icon: str = "🔗",
) -> None:
    """
    Renders a consistent empty-state info block across all pages.

    Args:
        message:      Primary message to display (supports markdown).
        icon:         Emoji icon shown in the info banner. Default: 📂
        action_label: Optional label for a page_link call-to-action.
        action_page:  Relative path to the page (e.g. "pages/2_Prepare_Data.py").
        action_icon:  Emoji icon for the page_link. Default: 🔗

    Why:
        All pages previously called st.info/st.warning individually with slightly
        different phrasing. This helper standardises the look, wording, and
        optional CTA link so every "nothing to show yet" message feels the same.

    Example:
        empty_state(
            "No forecast results yet. Click **Run Forecast** to generate predictions.",
            icon="🔮",
            action_label="Go to Prepare Data",
            action_page="pages/2_Prepare_Data.py",
            action_icon="🔧",
        )
    """
    st.info(f"{icon} {message}")
    if action_label and action_page:
        st.page_link(action_page, label=action_label, icon=action_icon)
