from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.domain.entities.dataset import DatasetStatus
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.dataset_repository import SQLAlchemyDatasetRepository
from app.infrastructure.storage.local_storage import LocalStorage
from app.services.dataset_service import DatasetService, UnsupportedFileTypeError, OversizedFileError, DatasetParsingError
from app.schemas.dataset import DatasetOut

from app.infrastructure.db.repositories.cleaning_log_repository import SQLAlchemyCleaningLogRepository
from app.services.cleaning_service import CleaningService
from app.services.feature_engineering_service import FeatureEngineeringService
import functools
import pandas as pd

@functools.lru_cache(maxsize=128)
def _get_headers_fast(path: str, mtime: float) -> list:
    """Cached fast reader for headers to prevent blocking uvicorn on every page load."""
    try:
        if path.lower().endswith(".csv"):
            return list(pd.read_csv(path, nrows=0).columns)
        elif path.lower().endswith(".xlsx"):
            # Use openpyxl directly to read only first row to avoid loading entire workbook
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheet = wb.active
            row = next(sheet.iter_rows(values_only=True))
            wb.close()
            return [str(c) for c in row if c is not None]
        else:
            return list(pd.read_excel(path, nrows=0).columns)
    except Exception:
        return []

router = APIRouter()

def get_dataset_service(db: Session = Depends(get_db)) -> DatasetService:
    """Dependency injector to construct DatasetService."""
    repo = SQLAlchemyDatasetRepository(db)
    storage = LocalStorage()
    return DatasetService(repo, storage)

def get_cleaning_service(db: Session = Depends(get_db)) -> CleaningService:
    """Dependency injector to construct CleaningService."""
    dataset_repo = SQLAlchemyDatasetRepository(db)
    cleaning_log_repo = SQLAlchemyCleaningLogRepository(db)
    storage = LocalStorage()
    return CleaningService(dataset_repo, cleaning_log_repo, storage)

def get_feature_engineering_service(db: Session = Depends(get_db)) -> FeatureEngineeringService:
    """Dependency injector to construct FeatureEngineeringService."""
    dataset_repo = SQLAlchemyDatasetRepository(db)
    storage = LocalStorage()
    return FeatureEngineeringService(dataset_repo, storage)

@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    POST route allowing authorized Analyst/Admin to upload datasets.
    Why: Validates headers, manages disk storage, and maps parsing errors.
    """
    try:
        content = await file.read()
        dataset = service.upload_dataset(
            user_id=current_user.id,
            filename=file.filename,
            content=content
        )
        from app.services.activity_log_service import log_activity
        log_activity(db, current_user.id, "dataset_uploaded", f"dataset_id={dataset.id}")
        return dataset
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DatasetParsingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OversizedFileError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_dataset(
    id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    DELETE route allowing dataset owner to delete dataset.
    Why: Owner-only deletion of physical file and database mapping.
    """
    repo = SQLAlchemyDatasetRepository(db)
    dataset = repo.get_by_id(id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    if dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Delete physical file
    import os
    import gc
    import time
    storage = LocalStorage()
    file_path = storage.get_path(dataset.storage_path)
    
    # Try robust cleanup for Windows file locking
    deleted_on_disk = False
    for _ in range(5):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            deleted_on_disk = True
            break
        except Exception:
            gc.collect()
            time.sleep(0.1)

    # Delete from DB
    repo.delete(id)

    # Log activity
    from app.services.activity_log_service import log_activity
    log_activity(db, current_user.id, "dataset_deleted", f"dataset_id={id}")

    return {"message": "Dataset deleted successfully"}

@router.get("", response_model=List[DatasetOut])
def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET route listings only own current authenticated user's datasets.
    Why: Assures resource segregation per identity.
    """
    repo = SQLAlchemyDatasetRepository(db)
    return repo.list_by_user(current_user.id)

@router.get("/{id}", response_model=DatasetOut)
def get_dataset(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET route providing single dataset by primary id key.
    Why: Rejects access (404) if data does not exist or does not belong to user.
    """
    repo = SQLAlchemyDatasetRepository(db)
    dataset = repo.get_by_id(id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # Extract actual column names from file on disk
    import os
    import pandas as pd
    from app.infrastructure.storage.local_storage import LocalStorage
    from app.schemas.dataset import DatasetOut

    storage = LocalStorage()
    file_path = storage.get_path(dataset.storage_path)
    # Check for cleaned or raw file fallback if referencing a featured dataset file
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

    columns = []
    if os.path.exists(file_path):
        try:
            mtime = os.path.getmtime(file_path)
            columns = _get_headers_fast(file_path, mtime)
        except Exception:
            pass

    return DatasetOut(
        id=dataset.id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        status=dataset.status,
        uploaded_at=dataset.uploaded_at,
        column_mapping=dataset.column_mapping,
        columns=columns
    )

@router.post("/{id}/clean", status_code=status.HTTP_200_OK)
def clean_dataset(
    id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: CleaningService = Depends(get_cleaning_service)
):
    """
    POST route triggering automated cleaning operations.
    Why: Restricts operations to Analyst/Admin roles and intercepts invalid IDs with 404.
    """
    # Verify dataset exists and belongs to the user first
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    try:
        summary, _ = service.clean(id)
        return summary
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during cleaning: {str(e)}"
        )

@router.post("/{id}/engineer-features", status_code=status.HTTP_200_OK)
def engineer_features(
    id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: FeatureEngineeringService = Depends(get_feature_engineering_service)
):
    """
    POST route triggering feature engineering calculations.
    Why: Rejects with 409 Conflict if status is not CLEANED, and with 404 if dataset does not exist/access denied.
    """
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    if dataset.status != DatasetStatus.CLEANED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset must be in CLEANED status. Current status: {dataset.status}"
        )

    try:
        summary = service.engineer_features(id)
        return summary
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during feature engineering: {str(e)}"
        )

from pydantic import BaseModel

class ColumnMappingUpdate(BaseModel):
    mapping: dict

@router.put("/{id}/mapping", status_code=status.HTTP_200_OK)
def update_column_mapping(
    id: int,
    body: ColumnMappingUpdate,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    PUT route updating column mappings configurations.
    Why: Validates that provided mapping key/value combinations match available dataframe schemas.
    """
    repo = SQLAlchemyDatasetRepository(db)
    dataset = repo.get_by_id(id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # 1. Validate mapping keys are subset of allowed semantic tags
    allowed_keys = {"date", "amount", "customer_id", "product", "region", "quantity"}
    mapping_data = body.mapping
    provided_keys = set(mapping_data.keys())
    if not provided_keys.issubset(allowed_keys):
        invalid = provided_keys - allowed_keys
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mapping semantic keys: {', '.join(invalid)}. Allowed: {', '.join(allowed_keys)}"
        )

    # 2. Validate column names exist in dataset headers
    import os
    storage = LocalStorage()
    file_path = storage.get_path(dataset.storage_path)
    # Check for cleaned or raw file fallback if referencing a featured dataset file
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source dataset file does not exist on disk"
        )

    try:
        import os
        mtime = os.path.getmtime(file_path)
        dataset_cols = set(_get_headers_fast(file_path, mtime))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read headers from source file: {str(e)}"
        )
    for role, col_name in mapping_data.items():
        if col_name not in dataset_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{col_name}' mapped to '{role}' does not exist in dataset headers: {', '.join(df.columns)}"
            )

    # 3. Save mapping
    dataset.column_mapping = mapping_data
    repo.update(dataset)
    return {"message": "Column mapping updated successfully", "column_mapping": mapping_data}


@router.post("/{id}/index", status_code=status.HTTP_200_OK)
def index_dataset(
    id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    POST route triggering extraction, chunking, embedding generation,
    and FAISS vector indexing of dataset KPIs, ML outputs, and raw samples.
    Why: Enables context building searches for downstream RAG queries.
    """
    # 1. Verify dataset access
    repo = SQLAlchemyDatasetRepository(db)
    dataset = repo.get_by_id(id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    from app.domain.entities.dataset import DatasetStatus
    if dataset.status not in (DatasetStatus.CLEANED, DatasetStatus.FEATURED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data preparation is required before analysis. Please clean the active dataset first."
        )

    # 2. Extract documents
    storage = LocalStorage()
    from app.services.context_builder_service import ContextBuilderService
    context_service = ContextBuilderService(db, repo, storage)
    documents = context_service.build_dataset_documents(id)

    # 3. Build persist path
    persist_dir = storage.get_path(os.path.join(str(current_user.id), str(id), "faiss_index"))

    # 4. Initialize model embeddings
    from app.core.config import settings
    from app.infrastructure.llm.embeddings import EmbeddingClient
    
    emb_client = EmbeddingClient(
        api_key=settings.gemini_api_key,
        model_name=settings.embedding_model_name
    )

    # 5. Build FAISS index on chunks
    from app.infrastructure.vectorstore.faiss_store import FaissVectorStore
    # Count chunks dynamically based on splitter
    chunks = []
    for doc in documents:
        chunks.extend(FaissVectorStore.chunk_text(doc))
    chunk_count = len(chunks)

    FaissVectorStore.build_index(
        documents=documents,
        embedding_client=emb_client,
        persist_dir=persist_dir
    )

    return {
        "message": "Dataset indexed successfully using FAISS vector store",
        "dataset_id": id,
        "document_count": len(documents),
        "chunk_count": chunk_count,
        "persist_dir": persist_dir
    }
