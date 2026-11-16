import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Enum, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from apps.api.app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def get_utc_now():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"


class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class MediaType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskType(str, enum.Enum):
    FACE_DEEPFAKE_IMAGE = "FACE_DEEPFAKE_IMAGE"
    FACE_DEEPFAKE_VIDEO = "FACE_DEEPFAKE_VIDEO"
    MULTIMODAL = "MULTIMODAL"


class PredictedClass(str, enum.Enum):
    LIKELY_MANIPULATED = "LIKELY_MANIPULATED"
    INCONCLUSIVE = "INCONCLUSIVE"
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"


class ModelStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    TRAINING = "TRAINING"
    EVALUATED = "EVALUATED"
    STAGED = "STAGED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    FAILED = "FAILED"


# --- MODELS ---

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    media_assets = relationship("MediaAsset", back_populates="owner", cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJob", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    detected_mime_type = Column(String(128), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), index=True, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    codec = Column(String(64), nullable=True)
    frame_rate = Column(Float, nullable=True)
    retention_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="media_assets")
    analysis_jobs = relationship("AnalysisJob", back_populates="media_asset", cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    media_asset_id = Column(String(36), ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    progress_percent = Column(Integer, default=0, nullable=False)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True)
    task_type = Column(Enum(TaskType), default=TaskType.FACE_DEEPFAKE_IMAGE, nullable=False)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    queued_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="analysis_jobs")
    media_asset = relationship("MediaAsset", back_populates="analysis_jobs")
    result = relationship("AnalysisResult", back_populates="analysis_job", uselist=False, cascade="all, delete-orphan")
    model_version = relationship("ModelVersion", back_populates="analysis_jobs")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    predicted_class = Column(Enum(PredictedClass), nullable=False)
    manipulation_score = Column(Float, nullable=False)
    threshold_low = Column(Float, default=0.35, nullable=False)
    threshold_high = Column(Float, default=0.65, nullable=False)
    aggregation_method = Column(String(64), default="top_k_mean", nullable=False)
    valid_frame_count = Column(Integer, default=0, nullable=False)
    face_frame_count = Column(Integer, default=0, nullable=False)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True)
    calibration_version = Column(String(64), default="v1.0", nullable=False)
    result_summary = Column(Text, nullable=True)
    provenance_status = Column(String(64), default="NOT_CHECKED", nullable=False)
    provenance_details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    analysis_job = relationship("AnalysisJob", back_populates="result")
    frame_results = relationship("FrameResult", back_populates="analysis_result", cascade="all, delete-orphan")


class FrameResult(Base):
    __tablename__ = "frame_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_result_id = Column(String(36), ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp_ms = Column(Integer, nullable=False)
    frame_index = Column(Integer, nullable=False)
    manipulation_score = Column(Float, nullable=False)
    face_detected = Column(Boolean, default=True, nullable=False)
    quality_status = Column(String(64), default="OK", nullable=False)
    box_coordinates = Column(JSON, nullable=True)
    explanation_artifact_key = Column(String(512), nullable=True)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="frame_results")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    version = Column(String(64), unique=True, nullable=False)
    task_type = Column(Enum(TaskType), default=TaskType.FACE_DEEPFAKE_IMAGE, nullable=False)
    architecture = Column(String(128), nullable=False)
    checkpoint_storage_key = Column(String(512), nullable=True)
    checkpoint_sha256 = Column(String(64), nullable=True)
    preprocessing_version = Column(String(64), default="v1.0", nullable=False)
    threshold_config_json = Column(JSON, nullable=True)
    status = Column(Enum(ModelStatus), default=ModelStatus.ACTIVE, nullable=False)
    evaluation_summary_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    retired_at = Column(DateTime, nullable=True)

    # Relationships
    analysis_jobs = relationship("AnalysisJob", back_populates="model_version")
    training_runs = relationship("TrainingRun", back_populates="model_version")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    version = Column(String(64), nullable=False)
    source_url = Column(String(512), nullable=True)
    license_or_terms_url = Column(String(512), nullable=True)
    permitted_use = Column(String(128), default="Research only", nullable=False)
    checksum_manifest = Column(String(64), nullable=True)
    sample_counts_json = Column(JSON, nullable=True)
    preprocessing_version = Column(String(64), default="v1.0", nullable=False)
    status = Column(String(64), default="READY", nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True)
    dataset_references = Column(JSON, nullable=True)
    code_commit_sha = Column(String(64), nullable=True)
    configuration_json = Column(JSON, nullable=True)
    random_seed = Column(Integer, default=42, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(64), default="COMPLETED", nullable=False)
    metrics_summary_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="training_runs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(128), nullable=False)
    target_type = Column(String(128), nullable=False)
    target_id = Column(String(64), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    ip_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")


# Compound indexes
Index("ix_analysis_jobs_status_queued_at", AnalysisJob.status, AnalysisJob.queued_at)
Index("ix_media_assets_owner_created", MediaAsset.owner_user_id, MediaAsset.created_at)
