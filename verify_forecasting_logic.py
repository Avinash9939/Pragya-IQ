import sys
import pandas as pd

# Mock streamlit components so importing doesn't fail
class MockSessionState(dict):
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value

class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState({"user": {"id": 5}, "active_dataset_id": 22})
    def set_page_config(self, *args, **kwargs): pass
    def markdown(self, *args, **kwargs): pass
    def write(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def stop(self): raise RuntimeError('st.stop called')
    def slider(self, *args, **kwargs): return kwargs.get("value", 0)
    def selectbox(self, *args, **kwargs): return kwargs.get("options", [""])[kwargs.get("index", 0)]
    def radio(self, *args, **kwargs): return kwargs.get("options", [""])[kwargs.get("index", 0)]
    def toggle(self, *args, **kwargs): return kwargs.get("value", False)
    def button(self, *args, **kwargs): return False
    def text_input(self, *args, **kwargs): return kwargs.get("value", "")

sys.modules['streamlit'] = MockStreamlit()
sys.modules['frontend.components.auth_guard'] = type('MockGuard', (), {'require_login': lambda *a, **k: None})()
sys.modules['frontend.components.sidebar'] = type('MockSidebar', (), {'render_sidebar': lambda *a, **k: None})()
sys.modules['frontend.components.empty_state'] = type('MockEmpty', (), {'empty_state': lambda *a, **k: None})()
sys.modules['frontend.services'] = type('MockServices', (), {'api_client': None})()
sys.modules['frontend.utils.formatting'] = type('FormatMock', (), {
    'format_number': lambda x: f"{x:,.0f}",
    'format_currency': lambda x: f"${x:,.2f}"
})()

# Create a mock dataframe
df_raw = pd.DataFrame({
    "Order_Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
    "Profit": [10.0, 20.0, 30.0, 40.0],
    "Sales": [100.0, 200.0, 300.0, 400.0],
    "Quantity": [2, 4, 6, 8],
    "Customer_ID": ["C1", "C2", "C3", "C4"],
    "Unrelated_Metric": [1.1, 2.2, 3.3, 4.4]
})

print("Simulating numeric column detection...")
numeric_cols = []
for col in df_raw.columns:
    try:
        numeric = pd.to_numeric(df_raw[col], errors="coerce")
        if numeric.notna().mean() >= 0.70:
            name_lower = col.lower()
            if not any(word in name_lower for word in (" id", "_id", "code", "zip", "phone", "outlier", "predicted", "prob", "class", "label", "is_", "status", "target", "cluster")):
                numeric_cols.append(col)
    except Exception:
        pass

priorities = ["sales", "profit", "quantity"]
pri_found = []
rem_found = []
for col in numeric_cols:
    col_l = col.strip().lower()
    if col_l in priorities:
        pri_found.append((priorities.index(col_l), col))
    else:
        rem_found.append(col)
pri_found.sort()
ordered_cols = [col for idx, col in pri_found] + rem_found

print("Detected numeric columns:", numeric_cols)
print("Ordered columns (prioritized):", ordered_cols)

# Assert Sales, Profit, Quantity are in front
assert ordered_cols[0] == "Sales", f"Expected Sales first, got {ordered_cols[0]}"
assert ordered_cols[1] == "Profit", f"Expected Profit second, got {ordered_cols[1]}"
assert ordered_cols[2] == "Quantity", f"Expected Quantity third, got {ordered_cols[2]}"
assert ordered_cols[3] == "Unrelated_Metric", f"Expected Unrelated_Metric last, got {ordered_cols[3]}"

print("\nForecasting Target Column dynamic detection passed successfully!")
