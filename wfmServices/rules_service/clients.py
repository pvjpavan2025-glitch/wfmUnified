"""
HTTP clients used by rules-service.
"""
from typing import Dict, Any, Optional
import os
import httpx
from shared.auth import token_manager


class SchedulerClient:
    def __init__(self, tenant_id: Optional[str] = None):
        # Default to docker service DNS; allow override via env SCHEDULER_SERVICE_URL
        self.base_url = os.getenv("SCHEDULER_SERVICE_URL", "http://scheduler-service:8004")
        self.timeout = 15
        self.tenant_id = tenant_id or os.getenv("DEFAULT_TENANT_ID", "default-tenant")

    def _headers(self) -> Dict[str, str]:
        # Mint a service token for calls
        access = token_manager.create_access_token({
            "user_id": "rules-service",
            "username": "rules",
            "tenant_id": self.tenant_id,
            "roles": ["admin"],
        })
        return {"Authorization": f"Bearer {access}", "Content-Type": "application/json"}

    async def create_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/jobs", json=job, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def schedule_job(self, job_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/jobs/{job_id}/schedule", headers=self._headers())
            r.raise_for_status()
            return r.json()
