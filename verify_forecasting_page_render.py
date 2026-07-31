import sys
import pandas as pd
from unittest.mock import MagicMock

class MockSessionState(dict):
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value

class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState({
            "active_dataset_id": "demo_sales_id",
            "forecast_result": {
                "historical": [{"ds": "2026-01-01", "y": 100.0}],
                "prophet": {
                    "forecast": [{"date": "2026-02-01", "yhat": 120.0, "yhat_lower": 100.0, "yhat_upper": 140.0}]
                }
            },
            "forecast_dataset_id": "demo_sales_id",
            "last_forecast_target": "Sales"
        })
    def set_page_config(self, *args, **kwargs): pass
    def markdown(self, *args, **kwargs): pass
    def write(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def success(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def stop(self): sys.exit(0)
    def slider(self, *args, **kwargs): return kwargs.get("value", 0)
    def selectbox(self, *args, **kwargs):
        opts = kwargs.get("options", [])
        if not opts:
            return None
        idx = kwargs.get("index", 0)
        if idx < 0 or idx >= len(opts):
            idx = 0
        return opts[idx]
    def radio(self, *args, **kwargs): return kwargs.get("options", [""])[kwargs.get("index", 0)]
    def toggle(self, *args, **kwargs): return kwargs.get("value", False)
    def button(self, *args, **kwargs): return False
    def text_input(self, *args, **kwargs): return kwargs.get("value", "")
    def page_link(self, *args, **kwargs): pass
    def columns(self, *args, **kwargs):
        return [MagicMock() for _ in (args[0] if isinstance(args[0], list) else range(args[0]))]
    def container(self, *args, **kwargs):
        return MagicMock()
    def plotly_chart(self, *args, **kwargs): pass
    def dataframe(self, *args, **kwargs): pass
    def spinner(self, *args, **kwargs):
        class SpinnerContext:
            def __enter__(self): pass
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return SpinnerContext()

from types import ModuleType
import importlib
original_reload = importlib.reload
importlib.reload = lambda m: original_reload(m) if isinstance(m, ModuleType) else m

sys.modules['streamlit'] = MockStreamlit()

auth_guard = ModuleType('auth_guard')
auth_guard.require_login = lambda *a, **k: ("demo_user", {})
sys.modules['frontend.components.auth_guard'] = auth_guard

sidebar = ModuleType('sidebar')
sidebar.render_sidebar = lambda *a, **k: None
sys.modules['frontend.components.sidebar'] = sidebar

empty_state = ModuleType('empty_state')
empty_state.empty_state = lambda *a, **k: None
sys.modules['frontend.components.empty_state'] = empty_state

class ApiError(Exception):
    def __init__(self, message="API Error", status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

mock_api_client = MagicMock()
mock_api_client.ApiError = ApiError

services = ModuleType('services')
services.api_client = mock_api_client
sys.modules['frontend.services'] = services

formatting = ModuleType('formatting')
formatting.format_number = lambda x: f"{x:,.0f}"
formatting.format_currency = lambda x: f"${x:,.2f}"
sys.modules['frontend.utils.formatting'] = formatting

sys.modules['plotly'] = MagicMock()
sys.modules['plotly.graph_objects'] = MagicMock()

# Mock components loader
import streamlit as st

# Mock filesystem / pandas loading to bypass file check of local load_dataframe_local
import os
os.path.exists = lambda x: True
os.listdir = lambda x: ["demo_sales_id_cleaned.csv"]

pd.read_csv = lambda *a, **k: pd.DataFrame({
    "Order_Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
    "Sales": [100.0, 200.0, 300.0, 400.0],
    "Cost": [80.0, 160.0, 240.0, 320.0],
    "Profit": [20.0, 40.0, 60.0, 80.0],
    "Quantity": [2, 4, 6, 8],
    "Product_Name": ["Gaming Laptop", "Mouse", "Keyboard", "Headphones"],
    "Region": ["East", "West", "North", "South"],
    "Category": ["Electronics", "Electronics", "Furniture", "Furniture"]
})
pd.read_excel = lambda *a, **k: pd.read_csv(*a, **k)

print("Mock environment initialized. Running 4_Forecasting.py main body...")
# Execute the pages file
try:
    with open('c:/Users/akkum/OneDrive/Desktop/Project/frontend/pages/4_Forecasting.py', encoding='utf-8') as f:
        exec(f.read(), globals())
    print("\nExec verification passed. No NameErrors or syntax errors encountered!")
except SystemExit:
    print("\nExec terminated gracefully via exit/st.stop.")
except Exception as e:
    import traceback
    err_str = traceback.format_exc()
    for line in err_str.splitlines():
        print("ERROR_LINE:", line.strip())
    sys.exit(1)
