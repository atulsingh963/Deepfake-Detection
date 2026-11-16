import os
import hashlib
import uuid
import shutil
from abc import ABC, abstractmethod
from typing import Tuple
from apps.api.app.core.config import settings

class StorageService(ABC):
    @abstractmethod
    def save_file(self, content: bytes, original_filename: str) -> Tuple[str, str, int]:
        """Returns (storage_key, sha256_hash, file_size_bytes)"""
        pass

    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        pass

class LocalStorageService(StorageService):
    def __init__(self, base_dir: str = settings.LOCAL_STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, content: bytes, original_filename: str) -> Tuple[str, str, int]:
        # Compute sha256
        sha256 = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        # Generate secure random UUID filename to prevent path traversal or shell exploits
        ext = os.path.splitext(original_filename)[1].lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        storage_key = unique_name
        dest_path = os.path.join(self.base_dir, storage_key)

        with open(dest_path, "wb") as f:
            f.write(content)

        return storage_key, sha256, file_size

    def get_file_path(self, storage_key: str) -> str:
        # Prevent path traversal
        clean_key = os.path.basename(storage_key)
        full_path = os.path.join(self.base_dir, clean_key)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Stored file {clean_key} not found")
        return full_path

    def delete_file(self, storage_key: str) -> bool:
        clean_key = os.path.basename(storage_key)
        full_path = os.path.join(self.base_dir, clean_key)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

# Default instance
storage_service = LocalStorageService()
