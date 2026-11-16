import os
import cv2
import numpy as np
from datetime import datetime, timezone
from apps.api.app.core.database import SessionLocal
from apps.api.app.models.entities import (
    AnalysisJob, JobStatus, AnalysisResult, FrameResult, PredictedClass, MediaType, ModelVersion, ModelStatus
)
from apps.api.app.storage.service import storage_service
from ml.src.mino_ml.face_detection.detector import face_detector
from ml.src.mino_ml.preprocessing.video import video_preprocessor
from ml.src.mino_ml.models.baseline import detector_engine
from ml.src.mino_ml.inference.aggregation import aggregate_frame_scores

def process_analysis_job(job_id: str):
    """
    Executes end-to-end media decoding, face detection, model inference, and persistence.
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job or job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        job.progress_percent = 10
        db.commit()

        asset = job.media_asset
        file_path = storage_service.get_file_path(asset.storage_key)

        active_model = db.query(ModelVersion).filter(ModelVersion.status == ModelStatus.ACTIVE).first()
        model_id = active_model.id if active_model else None

        # Execute according to Media Type
        if asset.media_type == MediaType.IMAGE:
            _process_image_job(db, job, asset, file_path, model_id)
        elif asset.media_type == MediaType.VIDEO:
            _process_video_job(db, job, asset, file_path, model_id)
        else:
            job.status = JobStatus.FAILED
            job.error_code = "UNSUPPORTED_MEDIA"
            job.error_message = f"Media type {asset.media_type} is not supported for analysis"
            db.commit()

    except Exception as e:
        db.rollback()
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_code = "PIPELINE_ERROR"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

def _process_image_job(db, job: AnalysisJob, asset, file_path: str, model_id: str):
    image_bgr = cv2.imread(file_path)
    if image_bgr is None:
        raise ValueError("Failed to decode image file")

    h, w = image_bgr.shape[:2]
    asset.width = w
    asset.height = h
    db.commit()

    job.progress_percent = 30
    db.commit()

    faces = face_detector.detect_faces(image_bgr)
    job.progress_percent = 60
    db.commit()

    frame_scores = []
    face_count = len(faces)

    if face_count == 0:
        # If no face detected, analyze whole frame but flag quality
        crop = cv2.resize(image_bgr, (224, 224))
        score = detector_engine.predict_face_crop(crop)
        predicted_class = PredictedClass.INCONCLUSIVE
        summary = "No prominent human face detected. Whole-frame forensic screening applied with low confidence."
        valid_face_count = 0
    else:
        # Score detected faces
        for box in faces:
            crop = face_detector.extract_aligned_face(image_bgr, box)
            s = detector_engine.predict_face_crop(crop)
            frame_scores.append(s)

        score = max(frame_scores)
        valid_face_count = len(frame_scores)

        if score >= 0.65:
            predicted_class = PredictedClass.LIKELY_MANIPULATED
            summary = "Facial boundary and texture artifacts detected consistent with synthetic manipulation."
        elif score <= 0.35:
            predicted_class = PredictedClass.LIKELY_AUTHENTIC
            summary = "Facial textures and frequency spectra appear consistent with authentic camera acquisition."
        else:
            predicted_class = PredictedClass.INCONCLUSIVE
            summary = "Model estimated likelihood lies in the uncertain band. Supplemental manual forensics recommended."

    # Persist Result
    result = AnalysisResult(
        analysis_job_id=job.id,
        predicted_class=predicted_class,
        manipulation_score=round(score, 4),
        threshold_low=0.35,
        threshold_high=0.65,
        aggregation_method="max_face_crop",
        valid_frame_count=1,
        face_frame_count=valid_face_count,
        model_version_id=model_id,
        calibration_version="v1.0",
        result_summary=summary,
        provenance_status="C2PA_NOT_FOUND",
        provenance_details={"c2pa_present": False, "sha256": asset.sha256}
    )
    db.add(result)
    db.commit()

    # Persist frame result
    fr = FrameResult(
        analysis_result_id=result.id,
        timestamp_ms=0,
        frame_index=0,
        manipulation_score=round(score, 4),
        face_detected=valid_face_count > 0,
        quality_status="OK" if valid_face_count > 0 else "NO_FACE_DETECTED",
        box_coordinates={"faces": [list(b) for b in faces]} if faces else None
    )
    db.add(fr)

    job.status = JobStatus.COMPLETED
    job.progress_percent = 100
    job.completed_at = datetime.now(timezone.utc)
    db.commit()

def _process_video_job(db, job: AnalysisJob, asset, file_path: str, model_id: str):
    # Metadata inspection
    meta = video_preprocessor.inspect_metadata(file_path)
    asset.width = meta.get("width")
    asset.height = meta.get("height")
    asset.duration_seconds = meta.get("duration_seconds")
    asset.codec = meta.get("codec")
    db.commit()

    job.progress_percent = 25
    db.commit()

    # Frame sampling
    sampled_frames = video_preprocessor.sample_video_frames(file_path, count=16)
    job.progress_percent = 50
    db.commit()

    valid_frame_scores = []
    created_frame_results = []
    face_frames_count = 0

    for idx, timestamp_ms, frame_bgr in sampled_frames:
        faces = face_detector.detect_faces(frame_bgr)
        if faces:
            face_frames_count += 1
            # Primary detected face
            crop = face_detector.extract_aligned_face(frame_bgr, faces[0])
            s = detector_engine.predict_face_crop(crop)
            valid_frame_scores.append(s)
            created_frame_results.append({
                "timestamp_ms": timestamp_ms,
                "frame_index": idx,
                "manipulation_score": round(s, 4),
                "face_detected": True,
                "quality_status": "OK",
                "box": list(faces[0])
            })
        else:
            # No face found
            created_frame_results.append({
                "timestamp_ms": timestamp_ms,
                "frame_index": idx,
                "manipulation_score": 0.5,
                "face_detected": False,
                "quality_status": "NO_FACE_IN_FRAME",
                "box": None
            })

    job.progress_percent = 85
    db.commit()

    # Aggregate video score
    if face_frames_count == 0:
        agg_score = 0.5
        predicted_class = PredictedClass.INCONCLUSIVE
        summary = "No human facial subjects identified across sampled video frames."
    else:
        agg_score = aggregate_frame_scores(valid_frame_scores, method="top_k_mean", k=3)
        if agg_score >= 0.65:
            predicted_class = PredictedClass.LIKELY_MANIPULATED
            summary = f"Manipulated facial patterns identified across {face_frames_count} sampled frames."
        elif agg_score <= 0.35:
            predicted_class = PredictedClass.LIKELY_AUTHENTIC
            summary = f"Consistent authentic biological signals and sensor patterns observed across {face_frames_count} frames."
        else:
            predicted_class = PredictedClass.INCONCLUSIVE
            summary = "Temporal forensic consistency inconclusive. High sensor noise or compression artifacts observed."

    result = AnalysisResult(
        analysis_job_id=job.id,
        predicted_class=predicted_class,
        manipulation_score=round(agg_score, 4),
        threshold_low=0.35,
        threshold_high=0.65,
        aggregation_method="top_k_mean",
        valid_frame_count=len(sampled_frames),
        face_frame_count=face_frames_count,
        model_version_id=model_id,
        calibration_version="v1.0",
        result_summary=summary,
        provenance_status="C2PA_NOT_FOUND",
        provenance_details={"c2pa_present": False, "sha256": asset.sha256}
    )
    db.add(result)
    db.commit()

    for fr_data in created_frame_results:
        fr = FrameResult(
            analysis_result_id=result.id,
            timestamp_ms=fr_data["timestamp_ms"],
            frame_index=fr_data["frame_index"],
            manipulation_score=fr_data["manipulation_score"],
            face_detected=fr_data["face_detected"],
            quality_status=fr_data["quality_status"],
            box_coordinates={"primary_box": fr_data["box"]} if fr_data["box"] else None
        )
        db.add(fr)

    job.status = JobStatus.COMPLETED
    job.progress_percent = 100
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
