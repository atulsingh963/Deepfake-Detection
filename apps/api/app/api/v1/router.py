from fastapi import APIRouter
from apps.api.app.api.v1 import auth, users, admin_users, media

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin_users.router)
api_router.include_router(media.router)
