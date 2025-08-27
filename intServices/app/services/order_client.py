from typing import Dict, Any, Optional
import time
import httpx
from jose import jwt
from ..core.config import settings

class OrderClient:
    def __init__(self):
        self.base_url = str(settings.order_api_base_url).rstrip("/")
        self.timeout = settings.order_api_timeout_seconds
        self.token = settings.order_api_token
        self.stub = settings.order_api_stub

    async def create_order(self, external_id: str, source: str, payload: Dict[str, Any], priority: str = "medium", description: str = None, customer_id: str = None) -> Dict[str, Any]:
        if self.stub:
            # Simulate a successful Order API response
            return {
                "id": f"ORDER-{external_id}",
                "_id": f"ORDER-{external_id}",
                "external_id": external_id,
                "source": source,
                "status": "pending",
                "payload": payload,
                "priority": priority,
                "description": description,
                "customer_id": customer_id,
                "processes": [],
                "total_tasks": 0,
                "completed_tasks": 0
            }
        headers = {"Content-Type": "application/json"}
        token = self.token
        if not token and settings.order_jwt_secret:
            # generate a short-lived JWT compatible with shared/auth
            payload_jwt = {
                "user_id": settings.order_user_id,
                "username": settings.order_username,
                "tenant_id": settings.order_tenant_id,
                "roles": settings.order_roles_list,
                "type": "access",
                "exp": int(time.time()) + settings.order_jwt_expire_minutes * 60,
            }
            token = jwt.encode(payload_jwt, settings.order_jwt_secret, algorithm=settings.order_jwt_alg)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"{self.base_url}/orders"
        
        # Extract order details from payload
        order_data = {
            "external_id": external_id,
            "source": source,
            "payload": payload,
            "priority": priority or payload.get("priority", "medium"),
            "description": description or payload.get("description", f"Order from {source}"),
            "customer_id": customer_id or payload.get("customer_id") or payload.get("customerId"),
            "status": "pending",
            "tenant_id": settings.order_tenant_id
        }
        
        # Add requested completion date if available
        if payload.get("requestedCompletionDate"):
            order_data["requested_completion_date"] = payload["requestedCompletionDate"]
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                url,
                json=order_data,
                headers=headers,
            )
            r.raise_for_status()
            return r.json()
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        if self.stub:
            return {
                "id": order_id,
                "external_id": f"EXT-{order_id}",
                "source": "test",
                "status": "pending",
                "processes": [],
                "total_tasks": 0,
                "completed_tasks": 0
            }
        
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        url = f"{self.base_url}/orders/{order_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
    
    async def get_order_with_processes(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order with detailed process and task information."""
        if self.stub:
            return {
                "id": order_id,
                "external_id": f"EXT-{order_id}",
                "source": "test",
                "status": "in_progress",
                "processes": [],
                "process_instances": [],
                "total_tasks": 3,
                "completed_tasks": 1
            }
        
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        url = f"{self.base_url}/orders/{order_id}/details"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
