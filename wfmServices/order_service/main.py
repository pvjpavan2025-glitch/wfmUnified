"""
Order Service main application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import structlog
from typing import List

from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user, TokenData
from .models import OrderCreate, OrderUpdate, OrderResponse
from .repository import OrderRepository
from .service import OrderService

logger = setup_logging("order-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Order Service")
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    logger.info("Order Service started successfully")
    yield
    logger.info("Shutting down Order Service")
    await db_manager.close()
    logger.info("Order Service shutdown complete")


app = FastAPI(
    title="WFM Order Service",
    description="Stores incoming orders and manages their lifecycle",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_order_service() -> OrderService:
    database = await db_manager.get_database()
    repo = OrderRepository(database)
    return OrderService(repo)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order-service"}


@app.post("/orders", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    svc: OrderService = Depends(get_order_service),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        data = order.dict()
        if not data.get("tenant_id"):
            data["tenant_id"] = current_user.tenant_id
        created = await svc.create_order(data, current_user.user_id)
        return OrderResponse(**created)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/orders/ready", response_model=List[OrderResponse])
async def list_ready_orders(
    skip: int = 0,
    limit: int = 100,
    svc: OrderService = Depends(get_order_service),
    current_user: TokenData = Depends(get_current_user)
):
    orders = await svc.list_ready(current_user.tenant_id, skip, limit)
    return [OrderResponse(**o) for o in orders]


@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_value: str,
    svc: OrderService = Depends(get_order_service),
    current_user: TokenData = Depends(get_current_user)
):
    updated = await svc.update_status(order_id, current_user.tenant_id, status_value)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(**updated)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("order_service.main:app", host="0.0.0.0", port=8008, reload=True)
