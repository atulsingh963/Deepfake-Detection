import os
from typing import Tuple
from apps.api.app.models.entities import MediaType
from apps.api.app.core.config import settings

# Magic byte signatures
SIGNATURES = {
    b"\xFF\xD8\xFF": ("image/jpeg", MediaType.IMAGE),
    b"\x89PNG\r\n\x1a\n": ("image/png", MediaType.IMAGE),
    b"RIFF": ("image/webp", MediaType.IMAGE),  # WebP begins RIFF....WEBP
    b"\x1a\x45\xdf\xa3": ("video/webm", MediaType.VIDEO), # Matroska/WebM
}

def validate_media_content(content: bytes, filename: str) -> Tuple[MediaType, str]:
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB")

    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if not ext:
        raise ValueError("File extension is missing")

    is_image = ext in settings.ALLOWED_IMAGE_EXTENSIONS
    is_video = ext in settings.ALLOWED_VIDEO_EXTENSIONS

    if not is_image and not is_video:
        raise ValueError(f"Unsupported file extension: .{ext}")

    # Check magic bytes
    if len(content) < 12:
        raise ValueError("File is too small or truncated")

    # Match magic signatures
    detected_mime = None
    detected_type = None

    if content.startswith(b"\xFF\xD8\xFF"):
        detected_mime = "image/jpeg"
        detected_type = MediaType.IMAGE
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
        detected_type = MediaType.IMAGE
    elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        detected_mime = "image/webp"
        detected_type = MediaType.IMAGE
    elif content.startswith(b"\x1a\x45\xdf\xa3"):
        detected_mime = "video/webm"
        detected_type = MediaType.VIDEO
    elif len(content) >= 8 and content[4:8] in [b"ftyp", b"moov", b"mdat", b"wide"]:
        # MP4 or MOV container
        detected_mime = "video/mp4" if ext != "mov" else "video/quicktime"
        detected_type = MediaType.VIDEO

    if not detected_mime or not detected_type:
        # Fallback based on extension if headers match common generic containers
        if is_image:
            detected_mime = f"image/{ext}"
            detected_type = MediaType.IMAGE
        elif is_video:
            detected_mime = f"video/{ext}"
            detected_type = MediaType.VIDEO
        else:
            raise ValueError("File signature does not match allowed forensic media types")

    return detected_type, detected_mime
