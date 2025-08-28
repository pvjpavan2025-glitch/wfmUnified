"""
Order Service FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Optional
from shared.auth import get_current_user
from shared.models import PaginationParams, SuccessResponse
from shared.database import db_manager
from .models import OrderCreate, OrderUpdate, OrderResponse
from .service import OrderService
from .repository import OrderRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await db_manager.connect_mongodb()
    yield
    # Shutdown
    await db_manager.close()


app = FastAPI(
    title="Order Service",
    description="Manages orders and their process relationships",
    version="1.0.0",
    lifespan=lifespan
)


async def get_order_service() -> OrderService:
    """Dependency injection for OrderService."""
    database = await db_manager.get_database()
    repository = OrderRepository(database)
    return OrderService(repository)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "order_service"}


@app.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Create a new order and trigger process identification."""
    return await service.create_order(order_data)


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Get order by ID."""
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Get all orders for a tenant."""
    pagination = PaginationParams(skip=skip, limit=limit)
    return await service.get_orders(pagination)


@app.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Update order."""
    order = await service.update_order(order_id, update_data)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.delete("/orders/{order_id}", response_model=SuccessResponse)
async def delete_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Delete order and associated processes."""
    success = await service.delete_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return SuccessResponse(message="Order deleted successfully")


@app.get("/orders/{order_id}/details")
async def get_order_with_processes(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Get order with detailed process and task information."""
    order_details = await service.get_order_with_processes(order_id)
    if not order_details:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_details


@app.post("/orders/{order_id}/refresh-progress", response_model=OrderResponse)
async def refresh_order_progress(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Refresh order progress based on current task status."""
    order = await service.update_order_progress(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
