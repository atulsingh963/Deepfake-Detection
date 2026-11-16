from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_password_hash, verify_password
from apps.api.app.core.jwt import create_access_token, create_refresh_token, decode_token
from apps.api.app.models.entities import User, UserRole, UserStatus, AuditLog
from apps.api.app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, UserResponse, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm
)
from apps.api.app.api.v1.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    user = User(
        email=user_in.email.lower(),
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,  # Can default to ACTIVE or PENDING based on admin approval setting
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    audit = AuditLog(
        actor_user_id=user.id,
        action="USER_REGISTER",
        target_type="user",
        target_id=user.id,
        metadata_json={"email": user.email}
    )
    db.add(audit)
    db.commit()

    return user

@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended")
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is pending admin approval")
    if user.status == UserStatus.DELETED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account has been deleted")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token_data = {"sub": user.id, "email": user.email, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload_in: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(payload_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    token_data = {"sub": user.id, "email": user.email, "role": user.role.value}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)):
    # In stateless JWT, clients drop tokens; server can log audit event
    return {"message": "Successfully logged out"}
