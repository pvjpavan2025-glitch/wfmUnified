"""
Repository for orders using MongoDB.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId

logger = structlog.get_logger(__name__)


class OrderRepository:
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.orders

    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data is None:
            return data
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data

    async def create_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        res = await self.collection.insert_one(data)
        data["_id"] = res.inserted_id
        return self._convert_id(data)

    async def get_by_id(self, order_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"_id": ObjectId(order_id), "tenant_id": tenant_id})
        return self._convert_id(doc) if doc else None

    async def get_by_external_id(self, external_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"external_id": external_id, "tenant_id": tenant_id})
        return self._convert_id(doc) if doc else None

    async def list_by_status(self, tenant_id: str, status: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"tenant_id": tenant_id, "status": status}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._convert_id(d) for d in docs]

    async def update_status(self, order_id: str, tenant_id: str, status: str) -> Optional[Dict[str, Any]]:
        await self.collection.update_one({"_id": ObjectId(order_id), "tenant_id": tenant_id}, {"$set": {"status": status, "updated_at": datetime.utcnow()}})
        return await self.get_by_id(order_id, tenant_id)
