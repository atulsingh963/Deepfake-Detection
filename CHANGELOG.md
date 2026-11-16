# Changelog

All notable changes to the **MINO Deepfake Detection & Media Forensics Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 8: Video Inference and Result Aggregation**
  - Sampling policy extracting 16 evenly distributed video frames with FFprobe stream analysis (`ml/src/mino_ml/preprocessing/video.py`).
  - Top-K risk aggregation, mean, and median aggregation policies (`ml/src/mino_ml/inference/aggregation.py`).
  - Comprehensive video-level analysis persisting frame results and timestamp risk profiles.
- **Phase 7: Baseline Image Detector and Model Interface**
  - Abstract `Detector` interface and concrete `EfficientNetBaselineDetector` using PyTorch EfficientNet-B0 with binary head.
  - Model metadata reporting architecture, checkpoint paths, and resolution configurations.
- **Phase 6: Media Preprocessing Pipeline**
  - OpenCV-based `FaceDetector` with facial landmark and aligned face extraction.
  - Fallback portrait ROI extraction to handle diverse frame sizes and resolutions.
- **Phase 5: Background Queue and Job Lifecycle**
  - Asynchronous job execution system (`services/worker/jobs/analysis.py` and `apps/api/app/tasks/queue.py`).
  - Progress updates tracking inspection, frame extraction, face detection, inference, and aggregation.
  - Endpoints: `POST /api/v1/analyses`, `GET /api/v1/analyses`, `GET /api/v1/analyses/{analysis_id}`, `DELETE /api/v1/analyses/{analysis_id}`.
  - Integration test `test_full_inference_pipeline_and_job_execution` verifying end-to-end media upload, queued execution, completion, and prediction results.
- **Phase 4: Secure Media Upload and Storage Abstraction**
  - Storage service interface (`StorageService`) with concrete `LocalStorageService` utilizing UUID naming.
  - Magic byte signatures and MIME type verification for JPEG, PNG, WebP, MP4, MOV, and WebM.
  - Secure media API endpoints: `POST /api/v1/media`, `GET /api/v1/media/{media_id}`, `GET /api/v1/media/{media_id}/file`, `DELETE /api/v1/media/{media_id}`.
- **Phase 3: Authentication and Role-Based Access Control**
  - JWT Access & Refresh token architecture using HS256 HMAC encryption.
  - Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- **Phase 2: Database, Migrations, and Core Architecture**
  - SQLAlchemy 2.0 models and Alembic migrations.
  - Database seed script creating initial administrator and active model.
- **Phase 1: Development Environment and Containers**
  - FastAPI service foundation and React Vite frontend.
- **Phase 0: Project Initialization**
  - Monorepo directory structure, `.gitignore`, `.env.example`, and architectural documentation.
