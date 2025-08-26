import httpx
import time
from jose import jwt
from typing import Dict, Any, List
from ..core.config import settings

class SchedulerClient:
    def __init__(self):
        self.base_url = str(settings.scheduler_api_base_url).rstrip("/")
        self.timeout = settings.scheduler_api_timeout_seconds
        self.token = settings.scheduler_api_token
        self.stub = settings.scheduler_api_stub

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = self.token
        if not token and settings.rules_jwt_secret:
            payload = {
                "user_id": settings.rules_user_id,
                "username": settings.rules_username,
                "tenant_id": settings.rules_tenant_id,
                "roles": settings.rules_roles_list,
                "type": "access",
                "exp": int(time.time()) + settings.rules_jwt_expire_minutes * 60,
            }
            token = jwt.encode(payload, settings.rules_jwt_secret, algorithm=settings.rules_jwt_alg)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def create_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        if self.stub:
            return {
                "id": job.get("external_id", "SIM-JOB-1"),
                "name": job.get("name", "Simulated Job"),
                "status": "pending",
                "tenant_id": job.get("tenant_id", settings.rules_tenant_id),
            }
        url = f"{self.base_url}/jobs"
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=job, headers=headers)
            r.raise_for_status()
            return r.json()

    async def schedule_job(self, job_id: str) -> Dict[str, Any]:
        if self.stub:
            return {
                "job_id": job_id,
                "analyst_id": "SIM-ANALYST-1",
                "start_time": "",
                "end_time": "",
                "confidence_score": 0.9,
            }
        url = f"{self.base_url}/jobs/{job_id}/schedule"
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, headers=headers)
            r.raise_for_status()
            return r.json()
