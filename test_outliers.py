import os
import pandas as pd

filepath = "../backend/storage/4/5_AI_BI_Master_Dataset_cleaned_features.csv"
if not os.path.exists(filepath):
    filepath = "backend/storage/4/5_AI_BI_Master_Dataset_cleaned_features.csv"

out_lines = []
out_lines.append(f"File exists: {os.path.exists(filepath)}")
if os.path.exists(filepath):
    try:
        df = pd.read_csv(filepath)
        out_lines.append(f"Loaded CSV shape: {df.shape}")
        outlier_cols = [c for c in df.columns if c.endswith("_outlier")]
        out_lines.append(f"Outlier columns: {outlier_cols}")
        for c in outlier_cols:
            dtype = df[c].dtype
            sum_val = df[c].sum()
            out_lines.append(f"Col: {c}, Dtype: {dtype}, Sum: {sum_val} (Type: {type(sum_val)})")
        
        # Test the sum expression
        total_sum = sum(df[c].sum() for c in outlier_cols)
        out_lines.append(f"Total outliers sum succeeded: {total_sum}")
    except Exception as e:
        out_lines.append(f"Error testing outliers: {str(e)}")

with open("out_test.txt", "w") as f:
    f.write("\n".join(out_lines))
