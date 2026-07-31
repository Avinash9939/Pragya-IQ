import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def train_churn_model(rfm_df: pd.DataFrame) -> Tuple[Any, pd.DataFrame, Dict[str, float]]:
    """
    Trains an XGBClassifier to predict churn probability from RFM columns.
    Why: Estimates churn risks, calculating standard classification quality metrics on test splits.
    """
    X = rfm_df[["Recency", "Frequency", "Monetary"]]
    y = rfm_df["churned"]

    total_samples = len(rfm_df)
    
    # Safe split handling for small datasets:
    if total_samples >= 5:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = XGBClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train)

    # Predict test split to evaluate
    preds_test = model.predict(X_test)
    
    # Calculate validation scores
    metrics = {
        "accuracy": float(accuracy_score(y_test, preds_test)),
        "precision": float(precision_score(y_test, preds_test, zero_division=0)),
        "recall": float(recall_score(y_test, preds_test, zero_division=0)),
        "f1": float(f1_score(y_test, preds_test, zero_division=0))
    }

    # Predict churn probability for ALL customers:
    # Class 1 probability represents churn risk
    prob_all = model.predict_proba(X)[:, 1]
    
    out_df = rfm_df.copy()
    out_df["churn_probability"] = prob_all.astype(float)

    return model, out_df, metrics
