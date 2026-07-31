import streamlit as st

def kpi_card(label: str, value: str, delta: str = None):
    """
    Renders a visually striking, premium KPI card component.
    Why: Uses Custom CSS from styles.css to deliver sleek borders, padding, and hover actions.
    """
    delta_html = ""
    if delta is not None:
        delta_str = str(delta).strip()
        is_down = delta_str.startswith("-")
        delta_class = "down" if is_down else "up"
        delta_html = f'<div class="kpi-delta {delta_class}">{"↓" if is_down else "↑"} {delta_str}</div>'
        
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
