import os
import sys
import pandas as pd
import numpy as np

os.chdir("frontend")

user_id = 5
active_id = 22
folder = f"../backend/storage/{user_id}"
print("Folder path:", os.path.abspath(folder))
try:
    files = os.listdir(folder)
    matches = [f for f in files if f.startswith(f"{active_id}_")]
    selected_file = matches[0]
    for suffix in ["_cleaned", "_features"]:
         for m in matches:
              if suffix in m: selected_file = m
    filepath = os.path.join(folder, selected_file)
    print("Resolved filepath:", filepath, "exists:", os.path.exists(filepath))
    df = pd.read_csv(filepath)
    print("Direct load success! Rows:", len(df))
except Exception as e:
    import traceback
    print("Direct load failed! Error:")
    traceback.print_exc()

sys.exit(0)
