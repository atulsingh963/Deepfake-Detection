# MINO Database Schema & Migrations

MINO uses SQLAlchemy 2.0 with Alembic migrations.

## Entity-Relationship Overview

```mermaid
erDiagram
    users ||--o{ media_assets : owns
    users ||--o{ analysis_jobs : initiates
    users ||--o{ audit_logs : triggers
    media_assets ||--o{ analysis_jobs : analyzed_in
    analysis_jobs ||--o| analysis_results : produces
    analysis_results ||--o{ frame_results : contains
    model_versions ||--o{ analysis_jobs : executes
    model_versions ||--o{ training_runs : evaluated_in
```

## Migration Commands
- Create migration: `alembic revision --autogenerate -m "migration_description"`
- Apply migration: `alembic upgrade head`
- Rollback migration: `alembic downgrade -1`
- Seed initial data: `python scripts/seed_db.py`
