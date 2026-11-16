import sys
import os

sys.path.insert(0, os.path.abspath("."))

from apps.api.app.core.config import settings
from apps.api.app.core.database import SessionLocal
from apps.api.app.core.security import get_password_hash
from apps.api.app.models.entities import User, UserRole, UserStatus, ModelVersion, ModelStatus, TaskType

def seed_db():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL).first()
        if not admin:
            admin = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name=settings.FIRST_SUPERUSER_NAME,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            db.add(admin)
            print(f"Created default admin user: {settings.FIRST_SUPERUSER_EMAIL}")
        else:
            print(f"Admin user already exists: {settings.FIRST_SUPERUSER_EMAIL}")

        # Check if default active model exists
        model = db.query(ModelVersion).filter(ModelVersion.version == settings.DEFAULT_MODEL_VERSION).first()
        if not model:
            model = ModelVersion(
                name=settings.DEFAULT_MODEL_NAME,
                version=settings.DEFAULT_MODEL_VERSION,
                task_type=TaskType.FACE_DEEPFAKE_IMAGE,
                architecture="EfficientNet-B0 / Xception Baseline",
                checkpoint_storage_key="data/models/mino_baseline_v1.pt",
                preprocessing_version="v1.0",
                threshold_config_json={"threshold_low": 0.35, "threshold_high": 0.65},
                status=ModelStatus.ACTIVE,
                evaluation_summary_json={
                    "roc_auc": 0.942,
                    "accuracy": 0.895,
                    "dataset": "FaceForensics++ / Celeb-DF Validation Baseline",
                    "note": "Probabilistic screening baseline model"
                }
            )
            db.add(model)
            print(f"Registered default active model: {settings.DEFAULT_MODEL_NAME} {settings.DEFAULT_MODEL_VERSION}")
        else:
            print(f"Model already registered: {settings.DEFAULT_MODEL_VERSION}")

        db.commit()
        print("Database seed completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
