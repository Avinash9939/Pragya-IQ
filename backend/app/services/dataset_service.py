import io
import pandas as pd
from typing import List, Optional
from datetime import datetime, timezone
from app.core.config import settings
from app.domain.entities.dataset import Dataset, DatasetStatus
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.infrastructure.storage.local_storage import LocalStorage

class UnsupportedFileTypeError(Exception):
    """Exception raised when an unsupported file type is uploaded."""
    pass

class OversizedFileError(Exception):
    """Exception raised when an uploaded file exceeds the configured size limit."""
    pass

class DatasetParsingError(Exception):
    """Exception raised when a dataset file fails parser analysis."""
    pass

class DatasetService:
    """
    Service orchestrating dataset validation, storage on disk, and DB metadata registration.
    Why: Dictates validation rules and decouples processing logic from API layer.
    """
    def __init__(self, dataset_repo: DatasetRepositoryInterface, storage_adapter: LocalStorage) -> None:
        self.dataset_repo = dataset_repo
        self.storage = storage_adapter

    def upload_dataset(self, user_id: int, filename: str, content: bytes) -> Dataset:
        """
        Validates, parses, persists, and stores a user raw dataset.
        Why: Evaluates size limits and file dimensions before DB insertion.
        """
        # Validate File Extension
        lower_name = filename.lower()
        if not (lower_name.endswith(".csv") or lower_name.endswith(".xlsx") or lower_name.endswith(".xls")):
            raise UnsupportedFileTypeError("File type not supported. Allowed formats: .csv, .xlsx, .xls")

        # Validate File Size
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.max_upload_size_mb:
            raise OversizedFileError(f"File size exceeds maximum limit of {settings.max_upload_size_mb}MB")

        # Analyze file details using Pandas
        try:
            if lower_name.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
            
            row_count = int(df.shape[0])
            column_count = int(df.shape[1])
        except Exception as e:
            raise DatasetParsingError(f"Error parsing dataset file: {str(e)}")

        # Register metadata on database
        new_dataset = Dataset(
            id=None,
            user_id=user_id,
            filename=filename,
            storage_path="pending_write",
            row_count=row_count,
            column_count=column_count,
            status=DatasetStatus.UPLOADED,
            uploaded_at=datetime.now(timezone.utc)
        )
        saved_dataset = self.dataset_repo.create(new_dataset)

        # Persist content body onto local storage using the user ID and assigned dataset ID
        storage_path = self.storage.save(user_id, saved_dataset.id, filename, content)

        # Update saved dataset storage path and status to VALIDATED
        saved_dataset.storage_path = storage_path
        saved_dataset.status = DatasetStatus.VALIDATED
        updated_dataset = self.dataset_repo.update(saved_dataset)

        return updated_dataset
