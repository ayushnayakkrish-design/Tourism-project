"""
Developer 2 — Storage Provider abstraction.

Design:
  - StorageProvider: abstract interface for uploading and storing images.
  - LocalStorageProvider: DEVELOPMENT-ONLY; stores files in storage/uploads/.
  - ProductionStorageProvider: can be extended to use S3, Cloudflare R2, Supabase, etc.

Business logic never directly calls os.path or open(); it uses StorageProvider.
This enables seamless migration from local dev to cloud storage without code changes.
"""
from __future__ import annotations

import abc
import hashlib
import os
from pathlib import Path
from typing import Optional

from fastapi import HTTPException


class StorageProvider(abc.ABC):
    """Abstract storage interface."""

    @abc.abstractmethod
    async def store_image(
        self, file_content: bytes, filename_hint: str, file_hash: Optional[str] = None
    ) -> str:
        """
        Store the image and return a publicly accessible URL or path reference.
        
        Args:
            file_content: raw image bytes
            filename_hint: suggested filename (may be ignored in cloud storage)
            file_hash: pre-computed SHA-256 hash; if None, computed here
            
        Returns:
            URL or reference string suitable for VisitProof.image_url
        """

    @abc.abstractmethod
    async def get_image_hash(self, image_url: str) -> Optional[str]:
        """
        Get the SHA-256 hash of an image.
        Useful for deduplication checks.
        Returns None if image not found or hash not available.
        """


class LocalStorageProvider(StorageProvider):
    """
    DEVELOPMENT-ONLY storage provider.
    
    Stores images in storage/uploads/ directory.
    Returns file:// URLs that work with file serving middleware or
    static file serving in development.
    
    WARNING: Not suitable for production. Use S3, R2, Supabase, etc. in production.
    """

    BASE_DIR = Path("storage/uploads")

    def __init__(self) -> None:
        self.BASE_DIR.mkdir(parents=True, exist_ok=True)

    async def store_image(
        self, file_content: bytes, filename_hint: str, file_hash: Optional[str] = None
    ) -> str:
        if not file_hash:
            file_hash = hashlib.sha256(file_content).hexdigest()

        # Use hash as filename to ensure uniqueness and enable deduplication
        ext = self._get_extension(filename_hint)
        filename = f"{file_hash}{ext}"
        path = self.BASE_DIR / filename

        # Write only if not already present
        if not path.exists():
            path.write_bytes(file_content)

        # Return a reference URL
        return f"file://{path.absolute()}"

    async def get_image_hash(self, image_url: str) -> Optional[str]:
        # Extract filename from file:// URL
        if not image_url.startswith("file://"):
            return None
        try:
            path = Path(image_url[7:])  # Remove 'file://'
            if not path.exists():
                return None
            content = path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except (OSError, IOError):
            return None

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract and validate extension from filename."""
        if not filename:
            return ".jpg"
        _, ext = os.path.splitext(filename.lower())
        allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        return ext if ext in allowed else ".jpg"


# Stub for production — implement with S3, Cloudflare R2, Supabase, etc.
class S3StorageProvider(StorageProvider):
    """Placeholder for S3 integration. Implement in future."""

    async def store_image(
        self, file_content: bytes, filename_hint: str, file_hash: Optional[str] = None
    ) -> str:
        raise NotImplementedError("S3StorageProvider not yet implemented")

    async def get_image_hash(self, image_url: str) -> Optional[str]:
        raise NotImplementedError("S3StorageProvider not yet implemented")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_storage_provider() -> StorageProvider:
    """Returns LocalStorageProvider for development."""
    # In production, check environment variables and return appropriate provider
    return LocalStorageProvider()
