import os
import json
import pandas as pd
from typing import List, Any
from sqlalchemy.orm import Session
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.infrastructure.db.repositories.kpi_result_repository import SQLAlchemyKpiResultRepository
from app.infrastructure.db.repositories.ml_repository import SQLAlchemyMlRunRepository
from app.infrastructure.storage.local_storage import LocalStorage

class ContextBuilderService:
    """
    Service coordinating document extraction for RAG pipelines.
    Why: Extracts relevant dataset metadata, computed KPIs, and raw samples instead of indexing massive databases.
    """
    def __init__(
        self,
        db: Session,
        dataset_repo: DatasetRepositoryInterface,
        storage_adapter: LocalStorage
    ) -> None:
        self.db = db
        self.dataset_repo = dataset_repo
        self.storage = storage_adapter
        self.kpi_repo = SQLAlchemyKpiResultRepository(db)
        self.ml_repo = SQLAlchemyMlRunRepository(db)

    def build_dataset_documents(self, dataset_id: int) -> List[str]:
        """
        Assembles list of text representations summarizing KPIs, ML runs, and raw rows.
        Returns: List of string documents ready for FAISS ingestion.
        """
        from app.domain.entities.dataset import DatasetStatus
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        if dataset.status not in (DatasetStatus.CLEANED, DatasetStatus.FEATURED):
            raise ValueError("Data preparation is required before analysis. Please clean the active dataset first.")

        documents = []

        # 1. Computed KPI Results
        kpis = self.kpi_repo.list_by_dataset_id(dataset_id)
        for k in kpis:
            kpi_doc = (
                f"Computed KPI Results for Dataset: {dataset.filename} (ID: {dataset_id})\n"
                f"KPI Type: {k.kpi_type}\n"
                f"Metrics Detail:\n{json.dumps(k.value_json, indent=2)}"
            )
            documents.append(kpi_doc)

        # 2. Latest ML Run Summaries/Metrics
        ml_runs = self.ml_repo.list_by_dataset_id(dataset_id)
        for r in ml_runs:
            run_doc = (
                f"Machine Learning Model Run for Dataset: {dataset.filename} (ID: {dataset_id})\n"
                f"Model Algorithm/Type: {r.model_type}\n"
                f"Configuration Parameters: {json.dumps(r.params_json)}\n"
                f"Validation/Accuracy Metrics:\n{json.dumps(r.metrics_json, indent=2)}"
            )
            documents.append(run_doc)

        # 3. Short sample of raw cleaned rows (20 rows)
        file_path = self.storage.get_path(dataset.storage_path)
        if os.path.exists(file_path):
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Draw sample
            sample_df = df.head(20)
            for idx, row in sample_df.iterrows():
                row_serial = ", ".join(f"{col}: {val}" for col, val in row.items())
                row_doc = (
                    f"Sample Data Record (Row Index: {idx}) for Dataset: {dataset.filename}\n"
                    f"Features: {row_serial}"
                )
                documents.append(row_doc)

        return documents
