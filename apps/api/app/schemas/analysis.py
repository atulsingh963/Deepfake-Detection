from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from apps.api.app.models.entities import JobStatus, TaskType, PredictedClass

class AnalysisJobCreate(BaseModel):
    media_asset_id: str
    task_type: Optional[TaskType] = None

class FrameResultResponse(BaseModel):
    timestamp_ms: int
    frame_index: int
    manipulation_score: float
    face_detected: bool
    quality_status: str
    box_coordinates: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    id: str
    predicted_class: PredictedClass
    manipulation_score: float
    threshold_low: float
    threshold_high: float
    aggregation_method: str
    valid_frame_count: int
    face_frame_count: int
    model_version_id: Optional[str] = None
    calibration_version: str
    result_summary: Optional[str] = None
    provenance_status: str
    created_at: datetime
    frame_results: List[FrameResultResponse] = []

    class Config:
        from_attributes = True

class AnalysisJobResponse(BaseModel):
    id: str
    owner_user_id: str
    media_asset_id: str
    status: JobStatus
    progress_percent: int
    model_version_id: Optional[str] = None
    task_type: TaskType
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[AnalysisResultResponse] = None

    class Config:
        from_attributes = True
