import pandas as pd

def compute_rfm(df: pd.DataFrame, customer_id_col: str, date_col: str, amount_col: str) -> pd.DataFrame:
    """
    Aggregates transaction logs to compile customer RFM parameters.
    Why: Converts unstructured logs into structured recency, frequency, monetary values.
    """
    temp_df = df.copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col])
    temp_df[amount_col] = temp_df[amount_col].astype(float)

    # Reference date: latest transaction date in dataset
    max_date = temp_df[date_col].max()

    # Compute metrics
    rfm = temp_df.groupby(customer_id_col).agg(
        Recency=(date_col, lambda x: (max_date - x.max()).days),
        Frequency=(date_col, 'count'),
        Monetary=(amount_col, 'sum')
    )

    return rfm
