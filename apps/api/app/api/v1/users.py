from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.models.entities import User, UserRole, UserStatus, AuditLog
from apps.api.app.schemas.auth import UserResponse, UserStatusUpdate, UserRoleUpdate
from apps.api.app.api.v1.deps import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None

@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name.strip()
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_user_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.status = UserStatus.DELETED
    db.commit()
    return {"message": "Account deactivated successfully"}
