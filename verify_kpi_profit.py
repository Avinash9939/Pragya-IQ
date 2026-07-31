import pandas as pd
import numpy as np

def compute_profit_kpi(df, schema):
    def safe_series(col_id):
        if not col_id or col_id not in df.columns:
            return pd.Series(0.0, index=df.index)
        series = df[col_id]
        if pd.api.types.is_numeric_dtype(series):
            return series.fillna(0.0)
        return pd.to_numeric(series.astype(str).str.replace(r'[^\d.-]', '', regex=True), errors="coerce").fillna(0.0)

    prof_col = next((c for c in df.columns if c.lower() == "profit"), schema.get("profit_col"))
    if prof_col and prof_col in df.columns:
        val = safe_series(prof_col).sum()
    else:
        sales_col = next((c for c in df.columns if c.lower() in ["sales", "revenue"]), schema.get("revenue_col"))
        cost_col = next((c for c in df.columns if c.lower() == "cost"), schema.get("cost_col"))
        val = safe_series(sales_col).sum() - safe_series(cost_col).sum()
    return val

# Test 1: Profit column is present
df1 = pd.DataFrame({"Profit": [10, 20, 30]})
val1 = compute_profit_kpi(df1, {})
print("Test 1 (Direct Profit):", val1)
assert val1 == 60

# Test 2: Profit column is string/currency
df2 = pd.DataFrame({"Profit": ["$10.00", "$20.00", "$30.00"]})
val2 = compute_profit_kpi(df2, {})
print("Test 2 (String Profit):", val2)
assert val2 == 60

# Test 3: Profit is absent, cost & sales are present
df3 = pd.DataFrame({"Sales": [100, 200, 300], "Cost": [80, 180, 250]})
val3 = compute_profit_kpi(df3, {})
print("Test 3 (Sales - Cost):", val3)
assert val3 == 90 # (100-80) + (200-180) + (300-250) = 20 + 20 + 50 = 90

print("\nVerification Passed Successfully!")
