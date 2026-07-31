import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.dataset_repository import SQLAlchemyDatasetRepository
from app.infrastructure.db.repositories.kpi_result_repository import SQLAlchemyKpiResultRepository
from app.infrastructure.storage.local_storage import LocalStorage
from app.services.kpi_service import KpiService, MissingColumnMappingError

router = APIRouter()

def get_kpi_service(db: Session = Depends(get_db)) -> KpiService:
    """Dependency injector to construct KpiService."""
    dataset_repo = SQLAlchemyDatasetRepository(db)
    kpi_result_repo = SQLAlchemyKpiResultRepository(db)
    storage = LocalStorage()
    return KpiService(dataset_repo, kpi_result_repo, storage)

def verify_dataset_ownership(dataset_id: int, current_user: User, db: Session) -> None:
    """Helper to verify dataset ownership."""
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

@router.get("/{dataset_id}/sales")
def get_sales_kpi(
    dataset_id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: KpiService = Depends(get_kpi_service)
):
    """GET sales KPI metrics."""
    verify_dataset_ownership(dataset_id, current_user, db)
    try:
        res = service.compute_sales_kpis(dataset_id)
        return res.value_json
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute sales KPIs: {str(e)}"
        )

@router.get("/{dataset_id}/customer")
def get_customer_kpi(
    dataset_id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: KpiService = Depends(get_kpi_service)
):
    """GET customer KPI metrics."""
    verify_dataset_ownership(dataset_id, current_user, db)
    try:
        res = service.compute_customer_kpis(dataset_id)
        return res.value_json
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute customer KPIs: {str(e)}"
        )

@router.get("/{dataset_id}/product")
def get_product_kpi(
    dataset_id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: KpiService = Depends(get_kpi_service)
):
    """GET product KPI metrics."""
    verify_dataset_ownership(dataset_id, current_user, db)
    try:
        res = service.compute_product_kpis(dataset_id)
        return res.value_json
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute product KPIs: {str(e)}"
        )

@router.get("/{dataset_id}/region")
def get_region_kpi(
    dataset_id: int,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: KpiService = Depends(get_kpi_service)
):
    """GET regional KPI metrics."""
    verify_dataset_ownership(dataset_id, current_user, db)
    try:
        res = service.compute_regional_kpis(dataset_id)
        return res.value_json
    except MissingColumnMappingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute regional KPIs: {str(e)}"
        )
