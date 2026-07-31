import pandas as pd
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("C:/Project/backend/storage/5/20_clean_AI_BI_Master_Dataset_cleaned.csv")
print("LEN:", len(df))
with open("debug_date.txt", "w") as f:
    for c in df.columns:
        try:
            parsed = pd.to_datetime(df[c], errors="coerce")
            ratio = parsed.notna().mean()
            nunique = df[c].nunique()
            f.write(f"{c} | {ratio:.4f} | {nunique}\n")
        except Exception as e:
            f.write(f"{c} | ERROR: {str(e)}\n")
