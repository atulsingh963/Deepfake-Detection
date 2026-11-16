# Changelog

All notable changes to the **MINO Deepfake Detection & Media Forensics Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Complete Platform Release

### Added
- **Phase 15: Containerization and Deployment**
  - Full multi-container Docker Compose configuration (`docker-compose.yml`) orchestrating `web`, `api`, `postgres`, and `redis`.
  - Production container recipes: `infra/docker/Dockerfile.api` (Python 3.12, FFmpeg, OpenCV) and `infra/docker/Dockerfile.web` (Node 20 multistage build on Nginx).
- **Phase 14: Security Hardening, Observability, and CI**
  - Continuous integration workflow (`.github/workflows/ci.yml`) automating migrations, database seeds, backend test passes, and frontend Vite builds.
  - Ownership protection guards across media assets, analysis jobs, and administrative capabilities.
- **Phase 13: Provenance and Optional Integrity Extension**
  - C2PA Content Credentials inspection module (`apps/api/app/services/provenance.py`) detecting JUMBF and provenance manifests.
  - Persistent SHA-256 asset fingerprinting stored alongside every forensic assessment.
- **Phase 12: Model Registry, Activation, and Rollback**
  - Administrative endpoints to activate, stage, and inspect registered model versions (`/api/v1/admin/model-versions`).
  - Active model dynamically linked to new incoming forensic analysis jobs.
- **Phase 11: Dataset Registry and Reproducible Model Evaluation**
  - Dataset registry endpoints (`/api/v1/admin/datasets`) and offline evaluation script (`ml/src/mino_ml/evaluation/evaluate.py`).
  - Computation of ROC-AUC, PR-AUC, accuracy, precision, recall, F1, and confusion matrices.
- **Phase 10: Admin Dashboard and User Management**
  - Admin summary console (`/api/v1/admin/dashboard/summary`) tracking system users, analysis volume, class ratios, and model states.
  - CSV export endpoint (`/api/v1/admin/exports/analyses.csv`) generating downloadable audit spreadsheets.
  - User authorization controls: activation, suspension, and role adjustments.
- **Phase 9: User Dashboard, History, and Reports**
  - Comprehensive React forensic workspace (`apps/web/src/App.tsx`) with dashboard metrics, interactive upload dropzone, analysis ledger, and frame risk timeline.
  - Downloadable PDF forensic reports (`apps/api/app/services/report.py` and `/api/v1/analyses/{id}/report`) with official disclaimer notices.
- **Phase 8: Video Inference and Result Aggregation**
  - 16-frame distributed sampling with FFprobe container inspection and Top-K risk aggregation.
- **Phase 7: Baseline Image Detector and Model Interface**
  - PyTorch EfficientNet-B0 baseline classifier with extensible `Detector` interface.
- **Phase 6: Media Preprocessing Pipeline**
  - Face detection, alignment, cropping, and fallback ROI extraction.
- **Phase 5: Background Queue and Job Lifecycle**
  - Asynchronous task execution with full progress tracking across QUEUED, PROCESSING, and COMPLETED states.
- **Phase 4: Secure Media Upload and Storage Abstraction**
  - MIME type and magic byte verification with UUID storage keys.
- **Phase 3: Authentication and Role-Based Access Control**
  - JWT access and refresh token management with secure bcrypt password hashing.
- **Phase 2: Database, Migrations, and Core Architecture**
  - Full relational schema in SQLAlchemy 2.0 with Alembic migrations and database seeds.
- **Phase 1: Development Environment and Containers**
  - FastAPI application with health probes and React TypeScript frontend.
- **Phase 0: Project Initialization**
  - Monorepo layout, specifications, `.editorconfig`, `.env.example`, and architectural documentation.
