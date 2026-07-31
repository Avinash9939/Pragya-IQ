import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime, timezone
from app.domain.entities.dataset import DatasetStatus, Dataset
from app.domain.entities.cleaning_log import CleaningLog
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.domain.interfaces.cleaning_log_repository import CleaningLogRepositoryInterface
from app.infrastructure.storage.local_storage import LocalStorage

class CleaningService:
    """
    Service executing dataset imputation, duplicate removal, and outlier flagging.
    Why: Encapsulates pandas cleaning computations to isolate from API controllers.
    """
    def __init__(
        self,
        dataset_repo: DatasetRepositoryInterface,
        cleaning_log_repo: CleaningLogRepositoryInterface,
        storage_adapter: LocalStorage
    ) -> None:
        self.dataset_repo = dataset_repo
        self.cleaning_log_repo = cleaning_log_repo
        self.storage = storage_adapter

    def clean(self, dataset_id: int) -> Tuple[Dict[str, Any], Dataset]:
        """
        Runs automated cleaning on dataset matching dataset_id.
        Why: Identifies empty cells, drops completely corrupt records, and calculates standard IQR outlier ranges.
        """
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        file_path = self.storage.get_path(dataset.storage_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Distinguish format parsing
        is_csv = file_path.lower().endswith(".csv")
        if is_csv:
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        rows_before = len(df)
        total_cols = len(df.columns)

        # 1. Report missing value locations
        missing_value_counts = {str(col): int(df[col].isna().sum()) for col in df.columns}

        # 2. Drop rows only if >50% of columns are empty
        non_na_threshold = total_cols - (total_cols // 2)
        df_dropped = df.dropna(thresh=non_na_threshold)
        rows_after_drops = len(df_dropped)

        # 3. Impute using median (numeric) & mode (categorical)
        df_filled = df_dropped.copy()
        for col in df_filled.columns:
            if df_filled[col].isna().all():
                if pd.api.types.is_numeric_dtype(df_filled[col].dtype):
                    df_filled[col] = df_filled[col].fillna(0)
                else:
                    df_filled[col] = df_filled[col].fillna("unknown")
                continue

            if pd.api.types.is_numeric_dtype(df_filled[col].dtype):
                median_val = df_filled[col].median()
                df_filled[col] = df_filled[col].fillna(median_val)
            else:
                mode_series = df_filled[col].mode()
                if not mode_series.empty:
                    mode_val = mode_series.iloc[0]
                    df_filled[col] = df_filled[col].fillna(mode_val)
                else:
                    df_filled[col] = df_filled[col].fillna("unknown")

        # 4. Remove duplicate rows
        df_no_duplicates = df_filled.drop_duplicates()
        rows_after_duplicates = len(df_no_duplicates)
        duplicates_removed = rows_after_drops - rows_after_duplicates

        # 5. Index outliers using IQR (lowerbound Q1-1.5*IQR, upperbound Q3+1.5*IQR) and flags them
        df_outliers = df_no_duplicates.copy()
        outliers_flagged = {}
        for col in df_outliers.columns:
            if pd.api.types.is_numeric_dtype(df_outliers[col].dtype) and not str(col).endswith("_outlier"):
                col_data = df_outliers[col]
                q1 = col_data.quantile(0.25)
                q3 = col_data.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                is_outlier = (col_data < lower_bound) | (col_data > upper_bound)
                df_outliers[f"{col}_outlier"] = is_outlier
                outliers_flagged[str(col)] = int(is_outlier.sum())

        rows_after = len(df_outliers)

        # 6. Suffix clean file write
        path_obj = Path(dataset.storage_path)
        # Suffix '_cleaned' right before the format extension, keeping extensions readable
        cleaned_path = path_obj.parent / f"{path_obj.stem}_cleaned{path_obj.suffix}"
        cleaned_storage_str = str(cleaned_path)

        resolved_cleanup_path = self.storage.get_path(cleaned_storage_str)
        if is_csv:
            df_outliers.to_csv(resolved_cleanup_path, index=False)
        else:
            df_outliers.to_excel(resolved_cleanup_path, index=False, engine="openpyxl")

        # 7. Update dataset model status to CLEANED
        dataset.status = DatasetStatus.CLEANED
        dataset.storage_path = cleaned_storage_str
        self.dataset_repo.update(dataset)

        # Calculate Data Quality Score
        total_rows = rows_before
        total_columns = total_cols
        total_cells = total_rows * total_columns
        
        missing_cells = sum(missing_value_counts.values())
        duplicate_rows = int(df.duplicated().sum())

        missing_percentage = (missing_cells / total_cells) * 100 if total_cells > 0 else 0.0
        duplicate_percentage = (duplicate_rows / total_rows) * 100 if total_rows > 0 else 0.0
        
        quality_score = 100.0 - (missing_percentage * 0.7) - (duplicate_percentage * 0.3)
        quality_score = max(0.0, min(100.0, float(quality_score)))
        
        quality_score = round(quality_score, 1)
        missing_percentage = round(missing_percentage, 2)
        duplicate_percentage = round(duplicate_percentage, 2)

        if quality_score >= 95:
            grade = "A+"
            quality_label = "Excellent"
        elif quality_score >= 90:
            grade = "A"
            quality_label = "Very Good"
        elif quality_score >= 80:
            grade = "B"
            quality_label = "Good"
        elif quality_score >= 70:
            grade = "C"
            quality_label = "Fair"
        elif quality_score >= 60:
            grade = "D"
            quality_label = "Pass"
        else:
            grade = "F"
            quality_label = "Poor"

        # Compile summaries
        summary = {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "missing_value_counts": missing_value_counts,
            "duplicates_removed": duplicates_removed,
            "outliers_flagged": outliers_flagged,
            "quality_score": quality_score,
            "grade": grade,
            "quality_label": quality_label,
            "missing_percentage": missing_percentage,
            "duplicate_percentage": duplicate_percentage,
            "penalty_breakdown": {
                "missing_percentage": missing_percentage,
                "duplicate_percentage": duplicate_percentage
            }
        }

        # Persist audit CleaningLog
        audit_log = CleaningLog(
            id=None,
            dataset_id=dataset_id,
            operation="auto_clean",
            details=summary,
            executed_at=datetime.now(timezone.utc)
        )
        self.cleaning_log_repo.create(audit_log)

        return summary, dataset
