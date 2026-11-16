import io
import time
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app
from apps.api.app.core.config import settings

@pytest.mark.asyncio
async def test_full_inference_pipeline_and_job_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        login_res = await client.post("/api/v1/auth/login", json={
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a synthetic test image with a drawing/circle simulating face structure
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        cv2.circle(img, (150, 150), 60, (200, 180, 150), -1)  # simulated face area
        cv2.circle(img, (130, 135), 10, (50, 50, 50), -1)    # eye
        cv2.circle(img, (170, 135), 10, (50, 50, 50), -1)    # eye
        cv2.ellipse(img, (150, 175), (20, 10), 0, 0, 180, (40, 40, 150), 3) # mouth
        _, encoded = cv2.imencode(".jpg", img)
        image_bytes = encoded.tobytes()

        # 1. Upload media
        upload_res = await client.post(
            "/api/v1/media",
            headers=headers,
            files={"file": ("test_forensic.jpg", io.BytesIO(image_bytes), "image/jpeg")}
        )
        assert upload_res.status_code == 201
        asset_id = upload_res.json()["id"]

        # 2. Trigger analysis job
        analysis_res = await client.post(
            "/api/v1/analyses",
            headers=headers,
            json={"media_asset_id": asset_id}
        )
        assert analysis_res.status_code == 202
        job_data = analysis_res.json()
        job_id = job_data["id"]
        assert job_data["status"] in ["QUEUED", "PROCESSING", "COMPLETED"]

        # 3. Poll for completion
        completed = False
        for _ in range(20):
            status_res = await client.get(f"/api/v1/analyses/{job_id}", headers=headers)
            assert status_res.status_code == 200
            current_job = status_res.json()
            if current_job["status"] == "COMPLETED":
                completed = True
                assert current_job["progress_percent"] == 100
                assert current_job["result"] is not None
                res = current_job["result"]
                assert 0.0 <= res["manipulation_score"] <= 1.0
                assert res["predicted_class"] in ["LIKELY_MANIPULATED", "INCONCLUSIVE", "LIKELY_AUTHENTIC"]
                assert len(res["frame_results"]) >= 1
                break
            elif current_job["status"] == "FAILED":
                pytest.fail(f"Analysis job failed: {current_job.get('error_message')}")
            time.sleep(0.5)

        assert completed, "Analysis job did not complete within the timeout period"
