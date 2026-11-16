from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from apps.api.app.models.entities import UserRole, UserStatus

class UserBase(BaseModel):
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: str
    role: UserRole
    status: UserStatus
    email_verified_at: Optional[datetime] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserStatusUpdate(BaseModel):
    status: UserStatus

class UserRoleUpdate(BaseModel):
    role: UserRole

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
