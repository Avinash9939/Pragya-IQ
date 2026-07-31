import pandas as pd
import numpy as np

def infer_forecast_mapping(df, existing_mapping=None):
    if df is None or df.empty:
        return None

    existing_mapping = existing_mapping or {}
    columns = list(df.columns)

    def is_valid_date(column):
        if column not in columns:
            return False
        parsed = pd.to_datetime(df[column], errors="coerce")
        return parsed.notna().mean() >= 0.70

    def is_valid_number(column):
        if column not in columns:
            return False
        numeric = pd.to_numeric(df[column], errors="coerce")
        return numeric.notna().mean() >= 0.70

    date_col = existing_mapping.get("date") if is_valid_date(existing_mapping.get("date")) else None
    amount_col = existing_mapping.get("amount") if is_valid_number(existing_mapping.get("amount")) else None

    lines = []
    lines.append("CHECKING EXISTING MAPPING:")
    lines.append(f"existing_mapping: {existing_mapping}")
    lines.append(f"date_col: {date_col}")
    lines.append(f"amount_col: {amount_col}")

    if not date_col:
        candidates = []
        for column in columns:
            name = column.lower()
            # Ignore date-decomposed feature columns or time parts
            if any(kw in name for kw in ("weekday", "year", "month", "day", "is_weekend")):
                lines.append(f"Skipping {column} because matches ignore keywords")
                continue
            is_named_date = any(word in name for word in ("date", "time", "timestamp", "month", "week", "period", "year", "day"))
            is_date_like = pd.api.types.is_datetime64_any_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(df[column])
            if not (is_named_date or is_date_like):
                continue
            parsed = pd.to_datetime(df[column], errors="coerce")
            valid_ratio = parsed.notna().mean()
            if valid_ratio >= 0.70 and parsed.nunique() >= 2:
                candidates.append((valid_ratio + (0.30 if is_named_date else 0), column))
                lines.append(f"Candidate date: {column} (score: {valid_ratio + (0.30 if is_named_date else 0)})")
        if candidates:
            date_col = max(candidates)[1]

    if not amount_col:
        candidates = []
        for column in columns:
            numeric = pd.to_numeric(df[column], errors="coerce")
            valid_ratio = numeric.notna().mean()
            name = column.lower()
            if valid_ratio < 0.70 or any(word in name for word in (" id", "_id", "code", "zip", "phone")):
                continue
            score = valid_ratio
            if any(word in name for word in ("revenue", "sales", "profit", "amount", "value", "cost", "income", "volume", "quantity", "count", "score")):
                score += 0.40
            candidates.append((score, column))
        if candidates:
            amount_col = max(candidates)[1]

    lines.append("FINAL INFERRED MAPPING:")
    lines.append(f"date_col: {date_col}")
    lines.append(f"amount_col: {amount_col}")
    
    with open("debug_mapping_raw.txt", "w") as out_f:
        out_f.write("\n".join(lines))

df = pd.read_csv("C:/Project/backend/storage/5/21_AI_BI_Master_Dataset.csv")
infer_forecast_mapping(df, {"date": "Order Date", "amount": "Sales"})
