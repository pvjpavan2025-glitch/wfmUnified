import httpx
import time
from jose import jwt
from typing import Dict, Any
from ..core.config import settings

class RulesClient:
    def __init__(self):
        self.base_url = str(settings.rules_api_base_url).rstrip("/")
        self.timeout = settings.rules_api_timeout_seconds
        self.token = settings.rules_api_token
        self.stub = settings.rules_api_stub

    async def create_order(self, payload: Dict[str, Any], orchestrate: bool = True, split_jobs: bool = False, auto_schedule: bool = True) -> Dict[str, Any]:
        if self.stub:
            # Simulate a successful Rules API response
            return {
                "status": "accepted",
                "id": payload.get("externalId", "SIM-ORDER-1"),
                "receivedItems": len(payload.get("serviceOrderItems", [])),
                "jobs": [] if not orchestrate else [{"id": "SIM-JOB-1"}],
                "schedules": [] if not orchestrate else [{"job_id": "SIM-JOB-1", "analyst_id": "SIM-AN-1"}],
            }
        headers = {"Content-Type": "application/json"}
        token = self.token
        if not token and settings.rules_jwt_secret:
            # generate a short-lived JWT compatible with shared/auth
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
        # Align with wfmServices rules-service endpoints; using /rules/evaluate to kick rules flow
        url = f"{self.base_url}/rules/evaluate"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                url,
                json={
                    "data": payload,
                    "orchestrate": orchestrate,
                    "split_jobs": split_jobs,
                    "auto_schedule": auto_schedule,
                },
                headers=headers,
            )
            r.raise_for_status()
            return r.json()
