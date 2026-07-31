import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from sklearn.preprocessing import LabelEncoder, StandardScaler
from app.domain.entities.dataset import DatasetStatus, Dataset
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.infrastructure.storage.local_storage import LocalStorage

class FeatureEngineeringService:
    """
    Service layer executing date parsing, categorical encoders, and StandardScaler scaling.
    Why: Centralizes pandas/scikit-learn feature modeling steps.
    """
    def __init__(self, dataset_repo: DatasetRepositoryInterface, storage_adapter: LocalStorage) -> None:
        self.dataset_repo = dataset_repo
        self.storage = storage_adapter

    def engineer_features(self, dataset_id: int) -> Dict[str, Any]:
        """
        Loads cleaned file from disk, builds ML features, and updates dataset record status.
        Why: Auto-detects column profiles (dates vs numeric vs category) and applies target estimators.
        """
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        if dataset.status != DatasetStatus.CLEANED:
            # Enforce sequential pipeline flow: must be cleaned first.
            raise ValueError("Dataset is not in CLEANED status")

        file_path = self.storage.get_path(dataset.storage_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Parse CSV or Excel
        is_csv = file_path.lower().endswith(".csv")
        if is_csv:
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        columns_added = []
        columns_encoded = {}
        columns_scaled = []

        # 1. Date/Datetime Decomposition
        date_cols = []
        for col in df.columns:
            col_str = str(col).lower()
            if "id" in col_str or col_str.endswith("_outlier"):
                continue

            s = df[col]
            is_date = False
            if pd.api.types.is_datetime64_any_dtype(s):
                is_date = True
            elif s.dtype == object:
                try:
                    s_str = s.dropna().astype(str)
                    if not s_str.str.isdigit().all():
                        parsed = pd.to_datetime(s, errors='coerce')
                        if parsed.notna().sum() > 0.5 * len(s):
                            is_date = True
                            df[col] = parsed
                except Exception:
                    pass

            if is_date:
                date_cols.append(col)

        new_date_features = []
        for col in date_cols:
            df[f"{col}_year"] = df[col].dt.year
            df[f"{col}_month"] = df[col].dt.month
            df[f"{col}_day"] = df[col].dt.day
            df[f"{col}_weekday"] = df[col].dt.weekday
            df[f"{col}_is_weekend"] = df[col].dt.weekday.isin([5, 6]).astype(int)

            decomposed = [
                f"{col}_year", f"{col}_month", f"{col}_day", f"{col}_weekday", f"{col}_is_weekend"
            ]
            new_date_features.extend(decomposed)
            columns_added.extend(decomposed)

            # Drop the original date column after decomposition
            df = df.drop(columns=[col])

        # 2. Categorical Variable Encoders
        categorical_cols = []
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col].dtype) and not str(col).endswith("_outlier"):
                categorical_cols.append(col)

        dummy_columns_created = []
        for col in categorical_cols:
            n_unique = df[col].nunique()
            if n_unique <= 15:
                # One-Hot Encoding Strategy
                # Why: One-hot avoids implying a false ordinal relationship for low-cardinality categories.
                columns_encoded[str(col)] = "one-hot"
                df_dummies = pd.get_dummies(df[col], prefix=col, dtype=int)
                new_dummies = list(df_dummies.columns)
                dummy_columns_created.extend(new_dummies)
                columns_added.extend(new_dummies)
                
                df = pd.concat([df.drop(columns=[col]), df_dummies], axis=1)
            else:
                # Label Encoding Strategy
                # Why: Label encoding avoids exploding dimensionality for high-cardinality categories.
                columns_encoded[str(col)] = "label"
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))

        # 3. Features Scaling via StandardScaler
        numeric_candidates = []
        for col in df.columns:
            col_str = str(col)
            col_lower = col_str.lower()

            if "id" in col_lower:
                continue
            if col_str in new_date_features:
                continue
            if col_str.endswith("_outlier"):
                continue
            if col_str in dummy_columns_created:
                continue

            if pd.api.types.is_numeric_dtype(df[col].dtype):
                numeric_candidates.append(col)

        if numeric_candidates:
            scaler = StandardScaler()
            df[numeric_candidates] = scaler.fit_transform(df[numeric_candidates].astype(float))
            columns_scaled.extend([str(c) for c in numeric_candidates])

        # 4. Save result to disk
        path_obj = Path(dataset.storage_path)
        features_path = path_obj.parent / f"{path_obj.stem}_features{path_obj.suffix}"
        features_storage_str = str(features_path)

        resolved_features_path = self.storage.get_path(features_storage_str)
        if is_csv:
            df.to_csv(resolved_features_path, index=False)
        else:
            df.to_excel(resolved_features_path, index=False, engine="openpyxl")

        # 5. Update DB status and paths
        dataset.status = DatasetStatus.FEATURED
        dataset.storage_path = features_storage_str
        self.dataset_repo.update(dataset)

        return {
            "columns_added": columns_added,
            "columns_encoded": columns_encoded,
            "columns_scaled": columns_scaled
        }
