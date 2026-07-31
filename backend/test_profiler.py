import pandas as pd
import numpy as np

import importlib
module = importlib.import_module("frontend.pages.8_AI_Performance_Intelligence")
detect_dataset_profile = module.detect_dataset_profile

def test_profiler():
    # 1. Retail Dataset
    df_retail = pd.DataFrame({
        "Product Name": ["Item A", "Item B"],
        "Order Date": ["2026-01-01", "2026-01-02"],
        "Sales": [100.0, 150.0]
    })
    p_retail = detect_dataset_profile(df_retail)
    print("Retail Profile:", p_retail)
    assert p_retail["context"] == "Retail"
    assert p_retail["entity_col"] == "Product Name"
    assert p_retail["metric_col"] == "Sales"
    assert p_retail["date_col"] == "Order Date"

    # 2. HR Dataset
    df_hr = pd.DataFrame({
        "Employee Name": ["John Doe", "Jane Smith"],
        "Join Date": ["2020-01-01", "2021-01-01"],
        "Salary": [50000, 60000]
    })
    p_hr = detect_dataset_profile(df_hr)
    print("HR Profile:", p_hr)
    assert p_hr["context"] == "Org Units"
    assert p_hr["entity_col"] == "Employee Name"
    assert p_hr["metric_col"] == "Salary"
    assert p_hr["date_col"] == "Join Date"

    # 3. Bank Dataset
    df_bank = pd.DataFrame({
        "Branch Location": ["North", "South"],
        "Transaction Time": ["2026-02-01 10:00:00", "2026-02-01 11:00:00"],
        "Amount": [10.5, 99.9]
    })
    p_bank = detect_dataset_profile(df_bank)
    print("Bank Profile:", p_bank)
    assert p_bank["context"] == "Branch Operations"
    assert p_bank["entity_col"] == "Branch Location"
    assert p_bank["metric_col"] == "Amount"
    assert p_bank["date_col"] == "Transaction Time"

    print("ALL PROFILER TESTS PASSED!")

if __name__ == "__main__":
    test_profiler()
