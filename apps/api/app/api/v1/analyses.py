from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.models.entities import (
    User, MediaAsset, AnalysisJob, JobStatus, TaskType, MediaType, ModelVersion, ModelStatus, AuditLog
)
from apps.api.app.schemas.analysis import AnalysisJobCreate, AnalysisJobResponse
from apps.api.app.tasks.queue import dispatch_job
from services.worker.jobs.analysis import process_analysis_job
from apps.api.app.api.v1.deps import get_current_user

router = APIRouter(prefix="/analyses", tags=["Analyses"])

@router.post("", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_analysis_job(
    job_in: AnalysisJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(MediaAsset).filter(MediaAsset.id == job_in.media_asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    if asset.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine default task type
    task_type = job_in.task_type
    if not task_type:
        task_type = TaskType.FACE_DEEPFAKE_IMAGE if asset.media_type == MediaType.IMAGE else TaskType.FACE_DEEPFAKE_VIDEO

    active_model = db.query(ModelVersion).filter(ModelVersion.status == ModelStatus.ACTIVE).first()
    model_version_id = active_model.id if active_model else None

    job = AnalysisJob(
        owner_user_id=current_user.id,
        media_asset_id=asset.id,
        status=JobStatus.QUEUED,
        progress_percent=0,
        model_version_id=model_version_id,
        task_type=task_type,
        queued_at=datetime.now(timezone.utc)
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to worker queue
    dispatch_job(process_analysis_job, job.id)

    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        action="ANALYSIS_SUBMITTED",
        target_type="analysis_job",
        target_id=job.id,
        metadata_json={"media_asset_id": asset.id, "task_type": task_type.value}
    )
    db.add(audit)
    db.commit()

    return job

@router.get("", response_model=List[AnalysisJobResponse])
def list_user_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AnalysisJob).filter(
        AnalysisJob.owner_user_id == current_user.id
    ).order_by(AnalysisJob.queued_at.desc()).offset(skip).limit(limit).all()

@router.get("/{analysis_id}", response_model=AnalysisJobResponse)
def get_analysis_details(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found")

    if job.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return job

@router.delete("/{analysis_id}", status_code=status.HTTP_200_OK)
def delete_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found")

    if job.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(job)
    db.commit()

    return {"message": "Analysis record deleted successfully"}
