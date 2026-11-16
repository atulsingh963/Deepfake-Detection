from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.models.entities import User, MediaAsset, AuditLog
from apps.api.app.schemas.media import MediaAssetResponse
from apps.api.app.storage.service import storage_service
from apps.api.app.storage.validator import validate_media_content
from apps.api.app.api.v1.deps import get_current_user

router = APIRouter(prefix="/media", tags=["Media Assets"])

@router.post("", response_model=MediaAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_media_asset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        content = await file.read()
        media_type, detected_mime = validate_media_content(content, file.filename or "upload")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))

    storage_key, sha256_hash, file_size = storage_service.save_file(content, file.filename or "file")

    media_asset = MediaAsset(
        owner_user_id=current_user.id,
        storage_key=storage_key,
        original_filename=file.filename or "uploaded_media",
        detected_mime_type=detected_mime,
        media_type=media_type,
        file_size_bytes=file_size,
        sha256=sha256_hash,
    )
    db.add(media_asset)
    db.commit()
    db.refresh(media_asset)

    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        action="MEDIA_UPLOAD",
        target_type="media_asset",
        target_id=media_asset.id,
        metadata_json={
            "sha256": sha256_hash,
            "filename": media_asset.original_filename,
            "size": file_size
        }
    )
    db.add(audit)
    db.commit()

    return media_asset

@router.get("/{media_id}", response_model=MediaAssetResponse)
def get_media_asset(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    
    # Ownership guard
    if asset.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return asset

@router.get("/{media_id}/file")
def download_media_file(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    if asset.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    file_path = storage_service.get_file_path(asset.storage_key)
    return FileResponse(file_path, media_type=asset.detected_mime_type, filename=asset.original_filename)

@router.delete("/{media_id}", status_code=status.HTTP_200_OK)
def delete_media_asset(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    if asset.owner_user_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Remove file on disk
    storage_service.delete_file(asset.storage_key)
    
    db.delete(asset)
    db.commit()

    return {"message": "Media asset deleted successfully"}
