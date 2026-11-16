import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app
from apps.api.app.core.config import settings

@pytest.mark.asyncio
async def test_auth_and_rbac_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Admin login
        login_res = await client.post("/api/v1/auth/login", json={
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD
        })
        assert login_res.status_code == 200
        admin_tokens = login_res.json()
        assert "access_token" in admin_tokens
        admin_token = admin_tokens["access_token"]

        # 2. Register normal user
        user_email = f"user_test_{settings.ENVIRONMENT}@test.local"
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Test Forensic Analyst"
        })
        assert reg_res.status_code in [201, 400]  # If already exists or created

        # 3. Login as normal user
        user_login_res = await client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": "Password123!"
        })
        assert user_login_res.status_code == 200
        user_tokens = user_login_res.json()
        user_token = user_tokens["access_token"]

        # 4. User profile endpoint
        profile_res = await client.get("/api/v1/users/me", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert profile_res.status_code == 200
        assert profile_res.json()["email"] == user_email

        # 5. RBAC check: Normal user attempting admin route must be 403 Forbidden
        rbac_res = await client.get("/api/v1/admin/users", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert rbac_res.status_code == 403

        # 6. Admin can access admin user list
        admin_list_res = await client.get("/api/v1/admin/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert admin_list_res.status_code == 200
        assert len(admin_list_res.json()) >= 1
