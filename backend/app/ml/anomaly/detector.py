import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def statistical_outliers(series: pd.Series, method: str = "iqr") -> pd.Series:
    """
    Identifies outliers using statistical methods (IQR or Z-Score).
    Why: Provides a baseline to compare against multi-dimensional ML models.
    """
    try:
        # Cast to float to handle bool/object columns cleanly
        series_numeric = pd.to_numeric(series.astype(float), errors="coerce")
    except Exception:
        series_numeric = pd.to_numeric(series, errors="coerce")

    series_clean = series_numeric.fillna(series_numeric.median() if series_numeric.notna().any() else 0.0)
    if method.lower() == "zscore":
        mean = series_clean.mean()
        std = series_clean.std()
        if std == 0 or pd.isna(std):
            return pd.Series(False, index=series.index)
        z_scores = (series_clean - mean) / std
        return abs(z_scores) > 3.0
    else:  # Default to IQR
        q1 = series_clean.quantile(0.25)
        q3 = series_clean.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0 or pd.isna(iqr):
            return pd.Series(False, index=series.index)
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return (series_clean < lower_bound) | (series_clean > upper_bound)

def isolation_forest_outliers(df: pd.DataFrame, feature_cols: list[str], contamination: float = 0.05) -> tuple[pd.Series, pd.Series]:
    """
    Identifies outliers using the Isolation Forest algorithm.
    Why: Detects multi-dimensional anomalies where features joint behavior is unusual.
    Returns:
        - boolean mask (True if outlier, False if inlier)
        - anomaly scores (Decision function value; lower/more negative means more anomalous)
    """
    X = df[feature_cols].copy()
    # Handle missing values cleanly
    for col in X.columns:
        try:
            X[col] = pd.to_numeric(X[col].astype(float), errors="coerce")
        except Exception:
            X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(X[col].median() if X[col].notna().any() else 0.0)
        
    clf = IsolationForest(contamination=contamination, random_state=42)
    preds = clf.fit_predict(X)
    
    # IsolationForest returns -1 for anomaly, 1 for inlier
    outlier_mask = pd.Series(preds == -1, index=df.index)
    scores = pd.Series(clf.decision_function(X), index=df.index)
    
    return outlier_mask, scores
