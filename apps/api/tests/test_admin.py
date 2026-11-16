import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app
from apps.api.app.core.config import settings

@pytest.mark.asyncio
async def test_admin_console_operations_and_reports():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as Admin
        admin_login = await client.post("/api/v1/auth/login", json={
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD
        })
        token = admin_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get dashboard summary
        summary_res = await client.get("/api/v1/admin/dashboard/summary", headers=headers)
        assert summary_res.status_code == 200
        summary = summary_res.json()
        assert "total_users" in summary
        assert "class_breakdown" in summary

        # 3. Register a research dataset
        ds_res = await client.post("/api/v1/admin/datasets", headers=headers, json={
            "name": "FaceForensics++ Test Bench",
            "version": "v3.0",
            "source_url": "https://github.com/ondyari/FaceForensics",
            "permitted_use": "Academic research"
        })
        assert ds_res.status_code == 201

        # 4. View datasets
        ds_list = await client.get("/api/v1/admin/datasets", headers=headers)
        assert ds_list.status_code == 200
        assert len(ds_list.json()) >= 1

        # 5. List model versions
        models_res = await client.get("/api/v1/admin/model-versions", headers=headers)
        assert models_res.status_code == 200
        assert len(models_res.json()) >= 1

        # 6. View audit logs
        audit_res = await client.get("/api/v1/admin/audit-logs", headers=headers)
        assert audit_res.status_code == 200
        assert len(audit_res.json()) >= 1

        # 7. Export analyses CSV
        csv_res = await client.get("/api/v1/admin/exports/analyses.csv", headers=headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
