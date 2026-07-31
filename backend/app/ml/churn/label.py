import pandas as pd

def derive_churn_label(rfm_df: pd.DataFrame, recency_threshold_days: int = 90) -> pd.DataFrame:
    """
    Labels customers as churned/active based on a recency threshold boundary.
    Why: Establishes a target binary variable for classification modeling.
    NOTE: The threshold is highly subjective and depends on business category:
          A coffee shop's "churn" window (e.g. 7-14 days) looks nothing like a car dealership's (e.g. 3-5 years).
          Thus, it is crucial to keep this threshold configurable and tune it per business domain.
    """
    out_df = rfm_df.copy()
    out_df["churned"] = (out_df["Recency"] > recency_threshold_days).astype(int)
    return out_df
