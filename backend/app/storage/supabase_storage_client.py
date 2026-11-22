from __future__ import annotations

import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class SupabaseStorageClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.supabase_url
        self.service_role_key = settings.supabase_service_role_key

    async def upload_pdf(self, bucket: str, path: str, content: bytes) -> str:
        """Upload PDF bytes to Supabase Storage."""
        url = f"{self.base_url}/storage/v1/object/{bucket}/{path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/pdf",
            "Cache-Control": "3600",
            "x-upsert": "true",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, content=content, headers=headers)
            resp.raise_for_status()
        logger.info("storage_upload_ok", bucket=bucket, path=path, size=len(content))
        return f"{bucket}/{path}"

    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Generate a signed URL for private bucket access."""
        url = f"{self.base_url}/storage/v1/object/sign/{bucket}/{path}"
        headers = {"Authorization": f"Bearer {self.service_role_key}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"expiresIn": expires_in}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return f"{self.base_url}/storage/v1{data['signedURL']}"


storage_client = SupabaseStorageClient()
