from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.models.entities import User, AnalysisJob, JobStatus
from apps.api.app.services.report import generate_pdf_forensic_report
from apps.api.app.schemas.analysis import AnalysisJobResponse
from apps.api.app.api.v1.deps import get_current_user

router = APIRouter(prefix="/analyses", tags=["Reports"])

@router.get("/{analysis_id}/report")
def download_pdf_report(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found")

    if job.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if job.status != JobStatus.COMPLETED or not job.result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analysis result is not yet available")

    # Serialize job to dict matching response schema
    job_resp = AnalysisJobResponse.model_validate(job).model_dump()
    pdf_bytes = generate_pdf_forensic_report(job_resp)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="MINO_Report_{analysis_id[:8]}.pdf"'}
    )
