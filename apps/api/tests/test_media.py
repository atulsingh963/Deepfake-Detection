import io
import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app
from apps.api.app.core.config import settings

@pytest.mark.asyncio
async def test_media_upload_security_and_ownership():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login user
        login_res = await client.post("/api/v1/auth/login", json={
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Reject invalid file extension
        bad_file = io.BytesIO(b"malicious payload")
        res_bad = await client.post(
            "/api/v1/media",
            headers=headers,
            files={"file": ("exploit.exe", bad_file, "application/octet-stream")}
        )
        assert res_bad.status_code == 415

        # 2. Upload valid synthetic JPEG image (starts with FF D8 FF)
        valid_jpeg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 100
        valid_file = io.BytesIO(valid_jpeg_bytes)
        res_upload = await client.post(
            "/api/v1/media",
            headers=headers,
            files={"file": ("sample_frame.jpg", valid_file, "image/jpeg")}
        )
        assert res_upload.status_code == 201
        data = res_upload.json()
        assert "id" in data
        assert data["original_filename"] == "sample_frame.jpg"
        assert data["media_type"] == "IMAGE"
        assert len(data["sha256"]) == 64
        asset_id = data["id"]

        # 3. Retrieve asset metadata
        res_get = await client.get(f"/api/v1/media/{asset_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["id"] == asset_id

        # 4. Download file bytes
        res_dl = await client.get(f"/api/v1/media/{asset_id}/file", headers=headers)
        assert res_dl.status_code == 200
        assert res_dl.content == valid_jpeg_bytes

        # 5. Delete asset
        res_del = await client.delete(f"/api/v1/media/{asset_id}", headers=headers)
        assert res_del.status_code == 200
