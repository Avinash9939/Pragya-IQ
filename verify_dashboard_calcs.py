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

sys.modules['streamlit'] = MockStreamlit()
sys.modules['frontend.components.auth_guard'] = type('MockGuard', (), {'require_login': lambda *a, **k: None})()
sys.modules['frontend.utils.formatting'] = type('FormatMock', (), {
    'format_number': lambda x: f"{x:,.0f}",
    'format_currency': lambda x: f"${x:,.2f}"
})()

# Import the schema detector from frontend
sys.path.append('frontend')
from utils.schema_detector import detect_schema, get_domain_kpis, compute_kpi

# Create double dataset simulating the real dirty dataset layout
df = pd.DataFrame({
    "Order_Date": ["2026-01-01", "2026-01-02", "2026-01-02", "2026-01-03"],
    "Sales": [100.0, 200.0, 300.0, 400.0],
    "Profit": [10.0, 20.0, 30.0, 40.0],
    "Customer_ID": ["C1", "C2", "C1", "C3"],
    "Order_ID": ["O1", "O2", "O2", "O3"],
    "Product": ["A", "B", "A", "C"],
    "Region": ["North", "South", "North", "East"],
    "Quantity": [2, 4, 6, 8],
    "Quantity_outlier": [False, False, False, False]
})

# Buggy mapping simulating backend's bad map
mock_mapping = {
    'date': 'Order_Date',
    'amount': 'Profit',         # hijacked by Profit in buggy state
    'customer_id': 'Customer_ID',
    'product': 'Product',
    'region': 'Region',
    'quantity': 'Quantity_outlier' # hijacked by outlier flag
}

print("Running Schema Detector on mock data...")
schema = detect_schema(df, mock_mapping)
print("Detected Schema:")
print("  revenue_col:", schema.get("revenue_col"))
print("  profit_col:", schema.get("profit_col"))
print("  quantity_col:", schema.get("quantity_col"))
print("  customer_col:", schema.get("customer_col"))
print("  order_col:", schema.get("order_col"))
print("  primary_metric:", schema.get("primary_metric"))

# Assert correctness
assert schema.get("revenue_col") == "Sales", f"Expected revenue_col 'Sales', got {schema.get('revenue_col')}"
assert schema.get("profit_col") == "Profit", f"Expected profit_col 'Profit', got {schema.get('profit_col')}"
assert schema.get("quantity_col") == "Quantity", f"Expected quantity_col 'Quantity', got {schema.get('quantity_col')}"

# Test KPI computation specs
specs = get_domain_kpis(schema, df)
print("\nKPI Specifications Proposed:")
for s in specs:
    print(f"  - Label: {s['label']}, Col: {s.get('col')}, Agg: {s.get('agg')}")

# Compute KPIs
kpis = {}
for s in specs:
    val, fmt = compute_kpi(df, s)
    kpis[s["label"]] = (val, fmt)

print("\nComputed KPIs:")
for k, v in kpis.items():
    print(f"  {k}: {v[1]} (raw: {v[0]})")

assert kpis["Total Revenue"][0] == 1000.0, f"Expected Revenue 1000.0, got {kpis['Total Revenue'][0]}"
assert kpis["Total Orders"][0] == 3, f"Expected 3 orders, got {kpis['Total Orders'][0]}"
assert kpis["Total Customers"][0] == 3, f"Expected 3 unique customers, got {kpis['Total Customers'][0]}"
assert kpis["Avg Order Value"][0] == 1000.0 / 3.0, f"Expected AOV 333.33, got {kpis['Avg Order Value'][0]}"

print("\nAll frontend calculations verified successfully!")
