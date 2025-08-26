"""
Order service business logic.
"""
from typing import List, Dict, Any, Optional
import structlog
from .repository import OrderRepository

logger = structlog.get_logger(__name__)


class OrderService:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    async def create_order(self, data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        data["created_by"] = created_by
        data["updated_by"] = created_by
        return await self.order_repo.create_order(data)

    async def list_ready(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        return await self.order_repo.list_by_status(tenant_id, "ready", skip, limit)

    async def update_status(self, order_id: str, tenant_id: str, status: str) -> Optional[Dict[str, Any]]:
        return await self.order_repo.update_status(order_id, tenant_id, status)
