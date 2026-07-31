import os
import pandas as pd
import numpy as np

active_id = 5
user_id = 4 # From previous dataset info

print("Simulating active dataset load...")
folder = f"backend/storage/{user_id}"
print(f"Folder exists: {os.path.exists(folder)}")

try:
    files = os.listdir(folder)
    matches = [f for f in files if f.startswith(f"{active_id}_")]
    print(f"Matches for ID {active_id}: {matches}")
    
    selected_file = matches[0]
    for suffix in ["_cleaned", "_features"]:
        for m in matches:
            if suffix in m:
                selected_file = m
    print(f"Selected processed file: {selected_file}")
    
    # Load df
    filepath = os.path.join(folder, selected_file)
    df = pd.read_csv(filepath)
    print(f"Loaded processed CSV shape: {df.shape}")
    
    # Load original raw df
    df_original = None
    selected_raw = matches[0]
    for m in matches:
        if "_cleaned" not in m and "_features" not in m and "_featured" not in m:
            selected_raw = m
            break
    raw_filepath = os.path.join(folder, selected_raw)
    df_original = pd.read_csv(raw_filepath)
    print(f"Loaded original CSV shape: {df_original.shape}")
    
    # Simulation calculations from 3_KPI_Dashboard.py
    rows_count = len(df)
    cols_count = len(df.columns)
    
    missing_original_count = int(df_original.isna().sum().sum()) if df_original is not None else 0
    duplicate_original_count = int(df_original.duplicated().sum()) if df_original is not None else 0
    
    missing_count = int(df.isna().sum().sum())
    duplicate_count = int(df.duplicated().sum())
    
    if rows_count > 0:
        missing_density = (missing_count / (rows_count * cols_count)) * 100 if cols_count > 0 else 0
        duplicate_ratio = (duplicate_count / rows_count) * 100
        penalty = (missing_density * 2.5) + (duplicate_ratio * 5.0)
        quality_score = max(0, min(100, int(100 - penalty)))
    else:
        quality_score = 100
        
    print(f"Calculations succeeded:")
    print(f"  Rows count: {rows_count}")
    print(f"  Cols count: {cols_count}")
    print(f"  Original missing: {missing_original_count}")
    print(f"  Original duplicates: {duplicate_original_count}")
    print(f"  Current missing: {missing_count}")
    print(f"  Current duplicates: {duplicate_count}")
    print(f"  Quality score: {quality_score}")
    
    # File size resolving
    fsize = os.path.getsize(filepath)
    if fsize > 1024 * 1024:
        size_str = f"{fsize / (1024 * 1024):.2f} MB"
    else:
        size_str = f"{fsize / 1024:.2f} KB"
    print(f"  Size string: {size_str}")
    
except Exception as e:
    import traceback
    print("CRITICAL SIMULATION ERROR:")
    traceback.print_exc()
