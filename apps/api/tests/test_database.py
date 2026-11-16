import pytest
from apps.api.app.core.database import SessionLocal
from apps.api.app.models.entities import User, ModelVersion, UserRole, ModelStatus

def test_seeded_data_exists():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        assert admin is not None
        assert admin.email == "admin@mino.local"

        model = db.query(ModelVersion).filter(ModelVersion.status == ModelStatus.ACTIVE).first()
        assert model is not None
        assert model.version == "v1.0.0"
    finally:
        db.close()
