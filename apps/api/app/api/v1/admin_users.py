from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.models.entities import User, UserRole, UserStatus, AuditLog
from apps.api.app.schemas.auth import UserResponse, UserStatusUpdate, UserRoleUpdate
from apps.api.app.api.v1.deps import require_admin

router = APIRouter(prefix="/admin", tags=["Admin Users"])

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[UserStatus] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    query = db.query(User)
    if status:
        query = query.filter(User.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: str,
    status_in: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.status = status_in.status
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        actor_user_id=admin.id,
        action="ADMIN_UPDATE_USER_STATUS",
        target_type="user",
        target_id=user.id,
        metadata_json={"new_status": user.status.value}
    )
    db.add(audit)
    db.commit()

    return user

@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    role_in: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = role_in.role
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        actor_user_id=admin.id,
        action="ADMIN_UPDATE_USER_ROLE",
        target_type="user",
        target_id=user.id,
        metadata_json={"new_role": user.role.value}
    )
    db.add(audit)
    db.commit()

    return user
