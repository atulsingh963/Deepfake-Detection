# Changelog

All notable changes to the **MINO Deepfake Detection & Media Forensics Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 4: Secure Media Upload and Storage Abstraction**
  - Storage service interface (`StorageService`) with concrete `LocalStorageService` utilizing UUID naming to prevent path traversal.
  - Magic byte signatures and MIME type verification for JPEG, PNG, WebP, MP4, MOV, and WebM (`apps/api/app/storage/validator.py`).
  - Strict upload limits enforced: maximum file size (100MB), allowable extensions, and media integrity calculations (SHA-256).
  - Secure media API endpoints: `POST /api/v1/media`, `GET /api/v1/media/{media_id}`, `GET /api/v1/media/{media_id}/file`, `DELETE /api/v1/media/{media_id}`.
  - Ownership protection: only file owners or administrators can access or delete uploaded media assets.
  - Automated tests in `apps/api/tests/test_media.py` verifying upload rejection of malicious binaries, valid upload processing, file streaming, and asset deletion.
- **Phase 3: Authentication and Role-Based Access Control**
  - JWT Access & Refresh token architecture (`apps/api/app/core/jwt.py`) using HS256 HMAC encryption.
  - Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`.
  - Profile endpoints: `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `DELETE /api/v1/users/me`.
  - Admin user endpoints: `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{user_id}/status`, `PATCH /api/v1/admin/users/{user_id}/role`.
  - Role-based authorization dependencies (`get_current_user`, `require_admin`).
  - React authentication interface with login/registration toggles, JWT local persistence, protected session header, and role-based views.
  - Integration tests for auth and RBAC in `apps/api/tests/test_auth.py` passing with 100% success.
- **Phase 2: Database, Migrations, and Core Architecture**
  - Complete SQLAlchemy 2.0 entities matching master specification: `users`, `media_assets`, `analysis_jobs`, `analysis_results`, `frame_results`, `model_versions`, `datasets`, `training_runs`, `audit_logs`.
  - Alembic migration environment initialized with automatic version generation and applied schema.
  - Safe native bcrypt password hashing module.
  - Database seed script (`scripts/seed_db.py`) creating default superuser and default active baseline model version.
  - Unit test verifying database connectivity and seeded data.
  - `docs/DATABASE.md` documenting schema and migration procedures.
- **Phase 1: Development Environment and Containers**
  - FastAPI application structure with `/health/live` and `/health/ready` endpoints.
  - Pydantic v2 settings management with `.env` reading and type validation.
  - Vite + React + TypeScript web app scaffold with Tailwind CSS v4, Lucide icons, and Recharts.
  - Proxy configuration in Vite for `/api` and `/health` requests to backend port 8000.
  - Production `docker-compose.yml` defining PostgreSQL 16 and Redis 7 container services with healthchecks.
  - Pytest test suite for health endpoints with AsyncClient (`pytest.ini` configured).
- **Phase 0: Project Initialization**
  - Monorepo directory structure established for API, Web, ML, and Services.
  - Project initialization with `.gitignore`, `.editorconfig`, `.env.example`, and architectural documentation.
  - Project scope and technical architecture guidelines matching master specification.
