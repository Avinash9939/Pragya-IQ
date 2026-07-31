import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, List

def explain_tree_model(model: Any, X: pd.DataFrame, feature_names: List[str]) -> tuple[List[Dict[str, float]], float]:
    """
    Computes SHAP explainability values for a tree-based model (regressor or classifier).
    Why: Visualizes predictive contributions per input feature.
    Returns:
        - List of dicts mapping {feature: contribution} per row.
        - The base value (expected value) of the model in float.
    """
    # 1. Initialize TreeExplainer
    explainer = shap.TreeExplainer(model)
    
    # 2. Compute SHAP values
    # For some sklearn or xgboost wrappers, it might return numpy array
    shap_output = explainer(X)
    shap_values = shap_output.values
    base_value = shap_output.base_values
    
    # 3. Handle expected/base value structure
    # For binary classification (XGBClassifier) under certain versions, base_values can be shape (2,) or (N, 2) or scaler or list
    if hasattr(base_value, "ndim") and base_value.ndim > 0:
        if base_value.ndim == 1:
            # If length is 2 (binary), take class 1
            if len(base_value) == 2:
                final_base_value = float(base_value[1])
            else:
                final_base_value = float(base_value[0])
        else:
            # shape (N, K)
            if base_value.shape[1] == 2:
                final_base_value = float(np.mean(base_value[:, 1]))
            else:
                final_base_value = float(np.mean(base_value[:, 0]))
    else:
        final_base_value = float(base_value)

    # 4. Handle SHAP values array structure
    # Multi-class/binary classifier can yield (N, F, 2) or (2, N, F) or list of length 2 of (N, F) or raw (N, F)
    # Let's inspect the shapes and convert to (N, F) matching index 1 class (for binary classifier)
    if isinstance(shap_values, list):
        if len(shap_values) == 2:
            # Binary classifier: take shape matching Class 1
            processed_shap = shap_values[1]
        else:
            processed_shap = shap_values[0]
    elif shap_values.ndim == 3:
        # Shape (N, F, 2) or (N, 2, F) or similar
        # For typical XGBClassifier: (N, F, 2) -> take slice [:, :, 1]
        if shap_values.shape[2] == 2:
            processed_shap = shap_values[:, :, 1]
        elif shap_values.shape[1] == 2:
            # format (N, 2, F) -> take [:, 1, :]
            processed_shap = shap_values[:, 1, :]
        else:
            processed_shap = shap_values[:, :, 0]
    else:
        # Binary classification with 1D output or regression
        processed_shap = shap_values

    # 5. Build per-row dictionary mappings
    explanations = []
    # If 1D array (e.g. single sample), convert to 2D
    if processed_shap.ndim == 1:
        processed_shap = np.expand_dims(processed_shap, axis=0)

    for i in range(len(X)):
        row_dict = {}
        for col_idx, feat in enumerate(feature_names):
            row_dict[feat] = float(processed_shap[i, col_idx])
        explanations.append(row_dict)

    return explanations, final_base_value
