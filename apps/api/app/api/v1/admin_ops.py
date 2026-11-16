from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io
from apps.api.app.core.database import get_db
from apps.api.app.models.entities import (
    User, AnalysisJob, AnalysisResult, PredictedClass, JobStatus, ModelVersion, Dataset, AuditLog, ModelStatus, TaskType
)
from apps.api.app.api.v1.deps import require_admin

router = APIRouter(prefix="/admin", tags=["Admin Analytics & Operations"])

class DatasetCreate(BaseModel):
    name: str
    version: str
    source_url: Optional[str] = None
    license_or_terms_url: Optional[str] = None
    permitted_use: str = "Research only"

class ModelVersionCreate(BaseModel):
    name: str
    version: str
    architecture: str
    task_type: TaskType = TaskType.FACE_DEEPFAKE_IMAGE
    checkpoint_storage_key: Optional[str] = None
    threshold_config_json: Optional[Dict[str, Any]] = None

@router.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    total_users = db.query(User).count()
    total_analyses = db.query(AnalysisJob).count()
    completed_analyses = db.query(AnalysisJob).filter(AnalysisJob.status == JobStatus.COMPLETED).count()
    failed_analyses = db.query(AnalysisJob).filter(AnalysisJob.status == JobStatus.FAILED).count()
    
    # Prediction distribution
    manipulated_count = db.query(AnalysisResult).filter(AnalysisResult.predicted_class == PredictedClass.LIKELY_MANIPULATED).count()
    authentic_count = db.query(AnalysisResult).filter(AnalysisResult.predicted_class == PredictedClass.LIKELY_AUTHENTIC).count()
    inconclusive_count = db.query(AnalysisResult).filter(AnalysisResult.predicted_class == PredictedClass.INCONCLUSIVE).count()

    active_model = db.query(ModelVersion).filter(ModelVersion.status == ModelStatus.ACTIVE).first()

    return {
        "total_users": total_users,
        "total_analyses": total_analyses,
        "completed_analyses": completed_analyses,
        "failed_analyses": failed_analyses,
        "class_breakdown": {
            "LIKELY_MANIPULATED": manipulated_count,
            "LIKELY_AUTHENTIC": authentic_count,
            "INCONCLUSIVE": inconclusive_count
        },
        "active_model": {
            "name": active_model.name if active_model else "None",
            "version": active_model.version if active_model else "None",
            "architecture": active_model.architecture if active_model else "None"
        }
    }

@router.get("/audit-logs")
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/exports/analyses.csv")
def export_analyses_csv(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    results = db.query(AnalysisResult).join(AnalysisJob).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Result ID", "Job ID", "Predicted Class", "Manipulation Score", 
        "Threshold Low", "Threshold High", "Valid Frames", "Face Frames", "Created At"
    ])

    for r in results:
        writer.writerow([
            r.id, r.analysis_job_id, r.predicted_class.value, r.manipulation_score,
            r.threshold_low, r.threshold_high, r.valid_frame_count, r.face_frame_count, r.created_at
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="MINO_Analyses_Export.csv"'}
    )

# Datasets Management
@router.get("/datasets")
def list_datasets(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return db.query(Dataset).all()

@router.post("/datasets", status_code=status.HTTP_201_CREATED)
def register_dataset(
    dataset_in: DatasetCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    dataset = Dataset(
        name=dataset_in.name,
        version=dataset_in.version,
        source_url=dataset_in.source_url,
        license_or_terms_url=dataset_in.license_or_terms_url,
        permitted_use=dataset_in.permitted_use,
        status="REGISTERED"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset

# Model Registry
@router.get("/model-versions")
def list_model_versions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return db.query(ModelVersion).all()

@router.post("/model-versions/{model_id}/activate")
def activate_model_version(
    model_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target_model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not target_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")

    # Deactivate current active models
    db.query(ModelVersion).filter(ModelVersion.status == ModelStatus.ACTIVE).update(
        {"status": ModelStatus.RETIRED, "retired_at": datetime.now(timezone.utc)}
    )

    target_model.status = ModelStatus.ACTIVE
    target_model.activated_at = datetime.now(timezone.utc)
    db.commit()

    # Audit
    audit = AuditLog(
        actor_user_id=admin.id,
        action="MODEL_ACTIVATED",
        target_type="model_version",
        target_id=target_model.id,
        metadata_json={"version": target_model.version}
    )
    db.add(audit)
    db.commit()

    return target_model
