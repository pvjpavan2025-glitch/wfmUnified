from typing import Dict, Any
import time
import httpx
from jose import jwt
from ..core.config import settings


class OrderClient:
    def __init__(self) -> None:
        # Default Order Service URL heuristic; allow ORDER_API_BASE_URL override if provided
        self.base_url = getattr(settings, "order_api_base_url", "http://localhost:8008").rstrip("/")
        self.timeout = getattr(settings, "order_api_timeout_seconds", 15)
        # Reuse rules token or dedicated one if present
        self.token = getattr(settings, "order_api_token", settings.rules_api_token)

    async def create_order(self, external_id: str, source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        token = self.token
        # If no static token provided, mint a short-lived JWT using shared settings
        if not token and getattr(settings, "rules_jwt_secret", ""):
            claims = {
                "user_id": getattr(settings, "rules_user_id", "integration-system"),
                "username": getattr(settings, "rules_username", "integration"),
                "tenant_id": getattr(settings, "rules_tenant_id", "default-tenant"),
                "roles": getattr(settings, "rules_roles_list", ["admin"]),
                "type": "access",
                "exp": int(time.time()) + getattr(settings, "rules_jwt_expire_minutes", 30) * 60,
            }
            token = jwt.encode(
                claims,
                settings.rules_jwt_secret,
                algorithm=getattr(settings, "rules_jwt_alg", "HS256"),
            )
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"{self.base_url}/orders"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                url,
                json={
                    "external_id": external_id,
                    "source": source,
                    "payload": payload,
                    "status": "ready",
                },
                headers=headers,
            )
            r.raise_for_status()
            return r.json()
