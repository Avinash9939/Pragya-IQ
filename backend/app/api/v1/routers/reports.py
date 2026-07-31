import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, require_role
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.dataset_repository import SQLAlchemyDatasetRepository
from app.infrastructure.db.repositories.report_repository import SQLAlchemyReportRepository
from app.services.report_service import ReportService
from app.schemas.report import ReportResponse

router = APIRouter()


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency injector to construct ReportService."""
    from app.infrastructure.db.repositories.dataset_repository import SQLAlchemyDatasetRepository
    from app.infrastructure.db.repositories.kpi_result_repository import SQLAlchemyKpiResultRepository
    from app.infrastructure.db.repositories.ml_repository import SQLAlchemyMlRunRepository, SQLAlchemyMlPredictionRepository
    from app.infrastructure.db.repositories.report_repository import SQLAlchemyReportRepository
    from app.api.v1.routers.ai import get_ai_service

    dataset_repo = SQLAlchemyDatasetRepository(db)
    kpi_repo = SQLAlchemyKpiResultRepository(db)
    ml_run_repo = SQLAlchemyMlRunRepository(db)
    ml_pred_repo = SQLAlchemyMlPredictionRepository(db)
    report_repo = SQLAlchemyReportRepository(db)
    ai_service = get_ai_service(db)

    return ReportService(
        dataset_repo=dataset_repo,
        kpi_repo=kpi_repo,
        ml_run_repo=ml_run_repo,
        ml_pred_repo=ml_pred_repo,
        ai_service=ai_service,
        report_repo=report_repo
    )


@router.post("/{dataset_id}/generate", response_model=ReportResponse, status_code=status.HTTP_200_OK)
def generate_report_endpoint(
    dataset_id: int,
    current_user: User = Depends(require_role(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service)
):
    """
    POST /reports/{dataset_id}/generate
    Generates a new Report document for the target dataset.
    Why: Assures tenancy constraints before launching ReportLab rendering.
    """
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    try:
        res = service.generate(dataset_id)
        
        from app.services.activity_log_service import log_activity
        log_activity(db, current_user.id, "report_generated", f"report_id={res.id}&dataset_id={dataset_id}")

        return res
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during report generation: {str(e)}"
        )


@router.get("/{id}/download", status_code=status.HTTP_200_OK)
def download_report_endpoint(
    id: int,
    current_user: User = Depends(require_role(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    GET /reports/{id}/download
    Downloads generated PDF report. Ensures caller owns dataset of report.
    Why: Rejects cross-tenant access with 404 to avoid metadata exposure leaks.
    """
    report_repo = SQLAlchemyReportRepository(db)
    report = report_repo.get_by_id(id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_by_id(report.dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    if not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file source lacks storage placement"
        )

    filename = os.path.basename(report.file_path)
    return FileResponse(
        path=report.file_path,
        filename=filename,
        media_type="application/pdf"
    )
