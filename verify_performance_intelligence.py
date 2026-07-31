import sys
import pandas as pd
import numpy as np

# Define mocks for streamlit components so importing doesn't fail
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
    def selectbox(self, label, options, *args, **kwargs): return options[0]
    def radio(self, label, options, *args, **kwargs): return options[0]
    def slider(self, label, *args, **kwargs): return 15
    def columns(self, *args, **kwargs): return [self] * (args[0] if isinstance(args[0], int) else len(args[0]))
    def metric(self, *args, **kwargs): pass
    def dataframe(self, *args, **kwargs): pass
    def plotly_chart(self, *args, **kwargs): pass
    def stop(self): raise RuntimeError('st.stop called')
    def info(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): print("STREAMLIT ERROR:", *args, **kwargs)
    def page_link(self, *args, **kwargs): pass
    def cache_data(self, func): return func

sys.modules['streamlit'] = MockStreamlit()
sys.modules['frontend.components.auth_guard'] = type('MockGuard', (), {'require_login': lambda *a, **k: None})()
sys.modules['frontend.components.sidebar'] = type('MockSidebar', (), {'render_sidebar': lambda *a, **k: None})()
sys.modules['frontend.components.empty_state'] = type('MockEmpty', (), {'empty_state': lambda *a, **k: None})()
sys.modules['frontend.services'] = type('MockServices', (), {'api_client': type('MockClient', (), {'get_dataset': lambda active_id: type('Dataset', (), {'column_mapping': {}})()})()})()
sys.modules['frontend.utils.formatting'] = type('MockFormatting', (), {'format_number': lambda x: str(x)})()

# Now import using importlib
import importlib
sys.path.append('frontend')
sys.path.append('backend')
mod = importlib.import_module('pages.8_AI_Performance_Intelligence')

print("Loaded 8_AI_Performance_Intelligence.py successfully under streamlit Mock!")

# Load dataset 22 and test detect_dataset_profile and analyze_trends
df = pd.read_csv('backend/storage/5/22_AI_BI_Master_Dataset_cleaned_features.csv')
p = mod.detect_dataset_profile(df)
print("Auto-detected profile:", p)
t = mod.analyze_trends(df, p['date_col'], p['amount_col'], p['entity_col'])
print("Total trend items calculated:", len(t))
if t:
    print("First trend item keys:", list(t[0].keys()))
    print("First trend items status:", t[0]['status'], ", slope:", t[0]['slope'])
