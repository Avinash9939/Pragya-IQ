import os
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.domain.entities.ml import MlRun, MlPrediction
from app.domain.entities.dataset import DatasetStatus
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.domain.interfaces.ml_repository import MlRunRepositoryInterface, MlPredictionRepositoryInterface
from app.infrastructure.storage.local_storage import LocalStorage
from app.services.kpi_service import MissingColumnMappingError
from app.ml.forecasting.prophet_model import run_prophet_forecast
from app.ml.forecasting.xgboost_model import run_xgboost_forecast


def _infer_forecast_columns(df: pd.DataFrame) -> tuple:
    """Return a trustworthy (date, numeric measure) pair for a stale mapping.

    This is intentionally schema-agnostic. Numeric fields are not considered
    dates only because pandas can coerce them to epoch timestamps.
    """
    date_candidates = []
    amount_candidates = []
    for column in df.columns:
        name = str(column).lower()
        is_date_named = any(token in name for token in ("date", "time", "timestamp", "month", "week", "period", "year", "day"))
        is_date_like = (pd.api.types.is_datetime64_any_dtype(df[column]) or
                        pd.api.types.is_object_dtype(df[column]) or
                        pd.api.types.is_string_dtype(df[column]))
        if is_date_named or is_date_like:
            parsed = pd.to_datetime(df[column], errors="coerce")
            valid_ratio = parsed.notna().mean()
            if valid_ratio >= 0.70 and parsed.nunique() >= 2:
                date_candidates.append((valid_ratio + (0.30 if is_date_named else 0), column))

        numeric = pd.to_numeric(df[column], errors="coerce")
        numeric_ratio = numeric.notna().mean()
        if numeric_ratio >= 0.70 and not any(token in name for token in (" id", "_id", "code", "zip", "phone", "outlier", "predicted", "prob", "class", "label", "is_", "status", "target", "cluster")):
            score = numeric_ratio
            if any(token in name for token in ("revenue", "sales", "profit", "amount", "value", "cost", "income", "volume", "quantity", "count", "score")):
                score += 0.40
            amount_candidates.append((score, column))

    if not date_candidates or not amount_candidates:
        return None, None
    return max(date_candidates)[1], max(amount_candidates)[1]


class MlService:
    """
    Service coordinating ML training, prediction processing, daily resampling, and run tracking validations.
    Why: Keeps forecasting wrappers decoupled from REST controllers.
    """
    def __init__(
        self,
        dataset_repo: DatasetRepositoryInterface,
        ml_run_repo: MlRunRepositoryInterface,
        ml_pred_repo: MlPredictionRepositoryInterface,
        storage_adapter: LocalStorage
    ) -> None:
        self.dataset_repo = dataset_repo
        self.ml_run_repo = ml_run_repo
        self.ml_pred_repo = ml_pred_repo
        self.storage = storage_adapter

    def run_forecast(self, dataset_id: int, horizon_days: int, model_type: str, cross_val: bool = True) -> Dict[str, Any]:
        """Loads dataset, resamples to daily timeseries, trains Prophet and/or XGBoost, and saves predictions."""
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        mapping = dataset.column_mapping or {}
        required = ["date", "amount"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        date_col = mapping["date"]
        amount_col = mapping["amount"]

        file_path = self.storage.get_path(dataset.storage_path)
        for suffix in ["_cleaned_features.csv", "_cleaned_features.xlsx"]:
            if suffix in file_path:
                clean_path = file_path.replace("_features", "")
                if os.path.exists(clean_path):
                    file_path = clean_path
                    break
                raw_path = file_path.replace("_cleaned_features", "")
                if os.path.exists(raw_path):
                    file_path = raw_path
                    break

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Load CSV or Excel
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Repair stale mappings generated from transformed/removed columns. This
        # happens after loading the real source schema, so a value such as
        # "Ship Mode_Same Day" can never survive as the date selection.
        is_amount_excluded = any(token in str(amount_col).lower() for token in ("outlier", "predicted", "prob", "class", "label", "is_", "status", "target", "cluster"))
        date_is_valid = date_col in df.columns and pd.to_datetime(df[date_col], errors="coerce").notna().mean() >= 0.70
        amount_is_valid = amount_col in df.columns and (not is_amount_excluded) and pd.to_numeric(df[amount_col], errors="coerce").notna().mean() >= 0.70
        if not date_is_valid or not amount_is_valid:
            inferred_date, inferred_amount = _infer_forecast_columns(df)
            if not inferred_date or not inferred_amount:
                raise ValueError(
                    "Forecasting requires a parseable date/time column and a numeric performance column. "
                    "Neither could be safely inferred from this dataset."
                )
            mapping = dict(mapping)
            mapping.update({"date": inferred_date, "amount": inferred_amount})
            dataset.column_mapping = mapping
            self.dataset_repo.update(dataset)
            date_col, amount_col = inferred_date, inferred_amount

        # Validate that the mapped 'date' column actually contains parseable dates
        # Sample up to 5 non-null values and try parsing them
        sample_vals = df[date_col].dropna().head(5).tolist()
        for sample_val in sample_vals:
            try:
                pd.to_datetime(sample_val)
            except Exception:
                raise ValueError(
                    f"The column mapped as 'Date' ('{date_col}') does not contain valid date values. "
                    f"Found value: '{sample_val}'. Please go to the Prepare Data page and re-configure "
                    f"your column mapping to select the correct date column."
                )

        # Aggregate to daily timeline
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except Exception as parse_err:
            raise ValueError(
                f"Cannot parse dates in column '{date_col}': {parse_err}. "
                f"Please go to the Prepare Data page and re-configure your column mapping."
            )
        daily_df = df.groupby(date_col)[amount_col].sum().reset_index()
        daily_df = daily_df.sort_values(date_col).copy()

        results = {}

        def execute_and_persist(m_type: str) -> Dict[str, Any]:
            shap_dict_list = None
            base_val = None

            if m_type == "prophet":
                forecast_df, metrics = run_prophet_forecast(daily_df, date_col, amount_col, horizon_days, cross_val)
            else:
                forecast_df, metrics, xgb_model, X_future, feat_names = run_xgboost_forecast(daily_df, date_col, amount_col, horizon_days, cross_val)
                try:
                    from app.ml.explainability.shap_explainer import explain_tree_model
                    shap_dict_list, base_val = explain_tree_model(xgb_model, X_future, feat_names)
                except Exception as ex:
                    # Defensive fallback if SHAP encounters mathematical anomalies
                    shap_dict_list = None
                    base_val = None

            # 1. Save MlRun
            run = MlRun(
                id=None,
                dataset_id=dataset_id,
                model_type=m_type,
                params_json={"horizon_days": horizon_days},
                metrics_json=metrics,
                created_at=datetime.now(timezone.utc)
            )
            saved_run = self.ml_run_repo.create(run)

            # 2. Save predictions batch
            predictions = []
            for i, row in forecast_df.iterrows():
                shap_payload = {
                    "yhat_lower": float(row['yhat_lower']),
                    "yhat_upper": float(row['yhat_upper'])
                }
                if shap_dict_list is not None and i < len(shap_dict_list):
                    shap_payload["shap_contributions"] = shap_dict_list[i]
                    shap_payload["base_value"] = base_val

                pred = MlPrediction(
                    id=None,
                    ml_run_id=saved_run.id,
                    entity_ref=row['date'],
                    prediction=float(row['yhat']),
                    shap_values_json=shap_payload
                )
                predictions.append(pred)

            self.ml_pred_repo.create_batch(predictions)

            return {
                "ml_run_id": saved_run.id,
                "metrics": metrics,
                "forecast": forecast_df.to_dict(orient="records")
            }

        # Select executing path
        m_lower = model_type.lower()
        if m_lower == "both":
            results["prophet"] = execute_and_persist("prophet")
            results["xgboost"] = execute_and_persist("xgboost")
        elif m_lower in ["prophet", "xgboost"]:
            results[m_lower] = execute_and_persist(m_lower)
        else:
            raise ValueError(f"Unsupported model type: {model_type}. Allowed: prophet, xgboost, both")

        # Expose historical actuals to let frontend chart render historical baseline line
        results["historical"] = [
            {"ds": row[date_col].strftime("%Y-%m-%d"), "y": float(row[amount_col])}
            for _, row in daily_df.iterrows()
        ]

        return results

    def run_segmentation(self, dataset_id: int, n_clusters: int = 4) -> Dict[str, Any]:
        """
        Runs customer RFM segmentation pipelines, persists run details/predictions,
        and scores clusters to assign semantic labels group tags.
        Why: Decouples segmentation models modeling from route controllers.
        """
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        mapping = dataset.column_mapping or {}
        required = ["customer_id", "date", "amount"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        cust_col = mapping["customer_id"]
        date_col = mapping["date"]
        amount_col = mapping["amount"]

        file_path = self.storage.get_path(dataset.storage_path)
        for suffix in ["_cleaned_features.csv", "_cleaned_features.xlsx"]:
            if suffix in file_path:
                clean_path = file_path.replace("_features", "")
                if os.path.exists(clean_path):
                    file_path = clean_path
                    break
                raw_path = file_path.replace("_cleaned_features", "")
                if os.path.exists(raw_path):
                    file_path = raw_path
                    break

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Load CSV or Excel
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # 1. Compute RFM metrics
        from app.ml.segmentation.rfm import compute_rfm
        rfm_df = compute_rfm(df, cust_col, date_col, amount_col)

        # 2. Run KMeans segmentation
        from app.ml.segmentation.kmeans_model import run_kmeans_segmentation
        segmented_df, inertia = run_kmeans_segmentation(rfm_df, n_clusters)

        # Ensure actual clusters fitted matches len
        actual_clusters = len(segmented_df['cluster'].unique())

        # 3. Labeling Logic:
        # We calculate cluster centroids (mean Recency, Frequency, Monetary).
        # We compute a Value Score to rank clusters:
        # Score = 0.5 * Mean Monetary + 0.3 * Mean Frequency - 0.2 * Mean Recency
        # High score means high spends, high frequency, low recency (champion).
        # Low score means low spends, low frequency, high recency (lost/inactive).
        centroids = segmented_df.groupby('cluster').mean()
        
        # Min-max scale the centroid means to normalize them between 0 and 1 (safeguarding against divide by zero)
        def norm_series(s):
            val_range = s.max() - s.min()
            if val_range == 0:
                return s * 0.0
            return (s - s.min()) / val_range

        norm_r = norm_bytes = norm_series(centroids['Recency'])
        norm_f = norm_series(centroids['Frequency'])
        norm_m = norm_series(centroids['Monetary'])

        # Compound score: Monetary (0.5) + Frequency (0.3) + Inverse Recency (0.2)
        centroids['score'] = (norm_m * 0.5) + (norm_f * 0.3) + ((1.0 - norm_r) * 0.2)

        # Rank clusters by score descending
        sorted_clusters = centroids.sort_values(by='score', ascending=False).index.tolist()

        # Dynamic label mapping:
        cluster_labels = {}
        for rank, cluster_id in enumerate(sorted_clusters):
            if actual_clusters == 1:
                label = "Total Base"
            elif actual_clusters == 2:
                label = "High Value" if rank == 0 else "At Risk / Lost"
            elif actual_clusters == 3:
                if rank == 0:
                    label = "Champions / High Value"
                elif rank == 1:
                    label = "Loyal / Mid Value"
                else:
                    label = "At Risk / Lost"
            else:
                if rank == 0:
                    label = "Champions / High Value"
                elif rank == 1:
                    label = "Loyal Customers"
                elif rank == 2:
                    label = "New / Potential Loyalists"
                else:
                    label = "At Risk / Lost"
            cluster_labels[cluster_id] = label

        # 4. Save MlRun
        run = MlRun(
            id=None,
            dataset_id=dataset_id,
            model_type="kmeans_segmentation",
            params_json={"n_clusters": n_clusters},
            metrics_json={
                "inertia": inertia,
                "cluster_sizes": {str(k): int(v) for k, v in segmented_df['cluster'].value_counts().items()},
                "cluster_labels": {str(k): v for k, v in cluster_labels.items()},
                "centroids": centroids[['Recency', 'Frequency', 'Monetary']].to_dict(orient="index")
            },
            created_at=datetime.now(timezone.utc)
        )
        saved_run = self.ml_run_repo.create(run)

        # 5. Save predictions (predictions represent cluster assignments per customer)
        predictions = []
        for cust_id, row in segmented_df.iterrows():
            pred = MlPrediction(
                id=None,
                ml_run_id=saved_run.id,
                entity_ref=str(cust_id),
                prediction=float(row['cluster']),
                shap_values_json={
                    "Recency": float(row['Recency']),
                    "Frequency": float(row['Frequency']),
                    "Monetary": float(row['Monetary']),
                    "Label": cluster_labels[int(row['cluster'])]
                }
            )
            predictions.append(pred)

        self.ml_pred_repo.create_batch(predictions)

        # Compile return payload format
        assignments = []
        for cust_id, row in segmented_df.iterrows():
            assignments.append({
                "customer_id": str(cust_id),
                "cluster": int(row['cluster']),
                "label": cluster_labels[int(row['cluster'])],
                "recency": float(row['Recency']),
                "frequency": float(row['Frequency']),
                "monetary": float(row['Monetary'])
            })

        return {
            "ml_run_id": saved_run.id,
            "metrics": {
                "inertia": inertia,
                "cluster_labels": {str(k): v for k, v in cluster_labels.items()}
            },
            "assignments": assignments
        }

    def run_churn_prediction(self, dataset_id: int, recency_threshold_days: int = None) -> Dict[str, Any]:
        """
        Runs XGBoost churn classification over customer RFM metrics.
        Why: Decouples churn classification modelling from API route controllers.
        """
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        mapping = dataset.column_mapping or {}
        required = ["customer_id", "date", "amount"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        cust_col = mapping["customer_id"]
        date_col = mapping["date"]
        amount_col = mapping["amount"]

        file_path = self.storage.get_path(dataset.storage_path)
        for suffix in ["_cleaned_features.csv", "_cleaned_features.xlsx"]:
            if suffix in file_path:
                clean_path = file_path.replace("_features", "")
                if os.path.exists(clean_path):
                    file_path = clean_path
                    break
                raw_path = file_path.replace("_cleaned_features", "")
                if os.path.exists(raw_path):
                    file_path = raw_path
                    break

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Resolve threshold setting
        if recency_threshold_days is None:
            from app.core.config import settings
            recency_threshold_days = settings.churn_config.get("recency_threshold_days", 90)

        # Load CSV or Excel
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # 1. Compute RFM features (reusing rfm module)
        from app.ml.segmentation.rfm import compute_rfm
        rfm_df = compute_rfm(df, cust_col, date_col, amount_col)

        # 2. Derive churn binary targets
        from app.ml.churn.label import derive_churn_label
        labeled_df = derive_churn_label(rfm_df, recency_threshold_days)

        # 3. Train classification model
        from app.ml.churn.model import train_churn_model
        model, output_df, metrics = train_churn_model(labeled_df)

        from app.ml.explainability.shap_explainer import explain_tree_model
        shap_dict_list, base_val = explain_tree_model(model, output_df[["Recency", "Frequency", "Monetary"]], ["Recency", "Frequency", "Monetary"])

        # 4. Save MlRun
        run = MlRun(
            id=None,
            dataset_id=dataset_id,
            model_type="xgboost_churn",
            params_json={"recency_threshold_days": recency_threshold_days},
            metrics_json=metrics,
            created_at=datetime.now(timezone.utc)
        )
        saved_run = self.ml_run_repo.create(run)

        # 5. Save prediction scores per customer
        predictions = []
        cust_ids = list(output_df.index)
        for i, cust_id in enumerate(cust_ids):
            row = output_df.loc[cust_id]
            pred = MlPrediction(
                id=None,
                ml_run_id=saved_run.id,
                entity_ref=str(cust_id),
                prediction=float(row['churn_probability']),
                shap_values_json={
                    "shap_contributions": shap_dict_list[i],
                    "base_value": base_val,
                    "features": {
                        "Recency": float(row['Recency']),
                        "Frequency": float(row['Frequency']),
                        "Monetary": float(row['Monetary'])
                    },
                    "churned_gt": int(row['churned'])
                }
            )
            predictions.append(pred)

        self.ml_pred_repo.create_batch(predictions)

        # Compile return predictions list
        out_preds = []
        for cust_id, row in output_df.iterrows():
            out_preds.append({
                "customer_id": str(cust_id),
                "churn_probability": float(row['churn_probability']),
                "churned": int(row['churned']),
                "recency": float(row['Recency']),
                "frequency": float(row['Frequency']),
                "monetary": float(row['Monetary'])
            })

        return {
            "ml_run_id": saved_run.id,
            "metrics": metrics,
            "predictions": out_preds
        }

    def run_anomaly_detection(self, dataset_id: int, contamination: float = 0.05) -> Dict[str, Any]:
        """
        Runs IsolationForest anomaly detection and IQR cross-referencing filters.
        Why: Decouples anomaly diagnostics logic from API routing endpoints.
        """
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        mapping = dataset.column_mapping or {}
        if "amount" not in mapping:
            raise MissingColumnMappingError(["amount"])

        amount_col = mapping["amount"]

        file_path = self.storage.get_path(dataset.storage_path)
        for suffix in ["_cleaned_features.csv", "_cleaned_features.xlsx"]:
            if suffix in file_path:
                clean_path = file_path.replace("_features", "")
                if os.path.exists(clean_path):
                    file_path = clean_path
                    break
                raw_path = file_path.replace("_cleaned_features", "")
                if os.path.exists(raw_path):
                    file_path = raw_path
                    break

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Load CSV or Excel
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Validate and repair amount mapping if invalid or if it contains excluded suffix
        name_lower = str(amount_col).lower() if amount_col else ""
        is_amount_excluded = any(token in name_lower for token in ("outlier", "predicted", "prob", "class", "label", "is_", "status", "target", "cluster"))
        
        amount_is_blank = not amount_col or amount_col not in df.columns
        amount_is_invalid = amount_is_blank or is_amount_excluded or pd.to_numeric(df[amount_col], errors="coerce").notna().mean() < 0.70
        
        if amount_is_invalid:
            inferred_date, inferred_amount = _infer_forecast_columns(df)
            if not inferred_amount:
                raise ValueError(
                    "Anomaly detection requires a numeric performance column (amount). "
                    "None could be safely inferred from this dataset."
                )
            mapping = dict(mapping)
            mapping.update({"amount": inferred_amount})
            if inferred_date:
                mapping.update({"date": inferred_date})
            dataset.column_mapping = mapping
            self.dataset_repo.update(dataset)
            amount_col = inferred_amount

        # Build feature columns list dynamically
        feature_cols = [amount_col]
        if "quantity" in mapping and mapping["quantity"] in df.columns:
            feature_cols.append(mapping["quantity"])

        # 1. Run Isolation Forest
        from app.ml.anomaly.detector import isolation_forest_outliers, statistical_outliers
        outlier_mask, scores = isolation_forest_outliers(df, feature_cols, contamination)

        # 2. Run statistical IQR cross-check over amount
        stat_mask = statistical_outliers(df[amount_col], method="iqr")

        # 3. Create MlRun
        run = MlRun(
            id=None,
            dataset_id=dataset_id,
            model_type="isolation_forest",
            params_json={"contamination": contamination},
            metrics_json={
                "contamination": contamination,
                "anomaly_count": int(outlier_mask.sum()),
                "iqr_outlier_count": int(stat_mask.sum())
            },
            created_at=datetime.now(timezone.utc)
        )
        saved_run = self.ml_run_repo.create(run)

        # 4. Save MlPrediction row for each FLAGGED anomaly
        predictions = []
        anomalies = []

        for idx, row in df.iterrows():
            is_anomaly = bool(outlier_mask.iloc[idx])
            score = float(scores.iloc[idx])
            is_statval = bool(stat_mask.iloc[idx])

            if is_anomaly:
                pred = MlPrediction(
                    id=None,
                    ml_run_id=saved_run.id,
                    entity_ref=str(idx),
                    prediction=score,
                    shap_values_json={
                        "flagged": True,
                        "iqr_outlier": is_statval,
                        "features": {col: float(row[col]) for col in feature_cols if col in row}
                    }
                )
                predictions.append(pred)

                # Compiles output dictionary
                record = row.to_dict()
                record["row_index"] = int(idx)
                record["anomaly_score"] = score
                record["iqr_outlier"] = is_statval
                anomalies.append(record)

        if predictions:
            self.ml_pred_repo.create_batch(predictions)

        return {
            "ml_run_id": saved_run.id,
            "metrics": {
                "contamination": contamination,
                "anomaly_count": len(anomalies),
                "iqr_outlier_count": int(stat_mask.sum())
            },
            "anomalies": anomalies
        }
