"""Business logic for Order Service."""
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from shared.models import PaginationParams
from .models import Order, OrderCreate, OrderUpdate, OrderResponse
from .repository import OrderRepository


class OrderService:
    """Service for order management."""
    
    def __init__(self, repository: OrderRepository):
        self.repository = repository
        self.rules_service_url = "http://localhost:8003"  # rules service
        self.process_service_url = "http://localhost:8008"  # process service

    async def create_order(self, order_data: OrderCreate) -> OrderResponse:
        """Create a new order and trigger process identification."""
        order = Order(**order_data.model_dump())
        created_order = await self.repository.create(order)
        
        # Trigger rules engine to identify processes for this order
        try:
            await self._trigger_process_identification(created_order)
        except Exception as e:
            print(f"Failed to trigger process identification: {e}")
        
        return OrderResponse(**created_order.model_dump())

    async def get_order(self, order_id: str, tenant_id: str) -> Optional[OrderResponse]:
        """Get order by ID."""
        order = await self.repository.get_by_id(order_id, tenant_id)
        return OrderResponse(**order.model_dump()) if order else None

    async def get_orders(self, tenant_id: str, pagination: PaginationParams) -> List[OrderResponse]:
        """Get all orders for a tenant with updated progress."""
        orders = await self.repository.get_all(tenant_id, pagination)
        order_responses = []
        
        for order in orders:
            # Update progress for each order
            try:
                updated_order = await self.update_order_progress(order.id, tenant_id)
                if updated_order:
                    order_responses.append(updated_order)
                else:
                    order_responses.append(OrderResponse(**order.model_dump()))
            except Exception as e:
                print(f"Failed to update progress for order {order.id}: {e}")
                order_responses.append(OrderResponse(**order.model_dump()))
        
        return order_responses

    async def update_order(self, order_id: str, tenant_id: str, update_data: OrderUpdate) -> Optional[OrderResponse]:
        """Update order."""
        order = await self.repository.update(order_id, tenant_id, update_data.model_dump(exclude_unset=True))
        return OrderResponse(**order.model_dump()) if order else None

    async def delete_order(self, order_id: str, tenant_id: str) -> bool:
        """Delete order and associated processes."""
        # Get order to check for associated processes
        order = await self.repository.get_by_id(order_id, tenant_id)
        if not order:
            return False
        
        # Cancel associated process instances
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.process_service_url}/orders/{order_id}/process-instances"
                )
                if response.status_code == 200:
                    process_instances = response.json()
                    for instance in process_instances:
                        if instance["status"] not in ["completed", "cancelled"]:
                            await client.post(
                                f"{self.process_service_url}/process-instances/{instance['id']}/cancel",
                                params={"reason": "Order deleted"}
                            )
        except Exception as e:
            print(f"Failed to cancel process instances: {e}")
        
        return await self.repository.delete(order_id, tenant_id)
    
    async def _trigger_process_identification(self, order: Order):
        """Trigger rules engine to identify processes for an order."""
        try:
            async with httpx.AsyncClient() as client:
                # Send order to rules engine for process identification
                response = await client.post(
                    f"{self.rules_service_url}/rules/evaluate",
                    json={
                        "data": {
                            "order_id": order.id,
                            "external_id": order.external_id,
                            "source": order.source,
                            "payload": order.payload,
                            "priority": order.priority,
                            "customer_id": order.customer_id
                        },
                        "orchestrate": True,
                        "auto_schedule": True
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Update order with identified processes
                    process_ids = [job.get("process_id") for job in result.get("jobs", []) if job.get("process_id")]
                    if process_ids:
                        await self.repository.update(
                            order.id,
                            order.tenant_id,
                            {"processes": process_ids}
                        )
        except Exception as e:
            print(f"Process identification failed: {e}")
            raise
    
    async def get_order_with_processes(self, order_id: str, tenant_id: str) -> Optional[dict]:
        """Get order with detailed process and task information."""
        order = await self.repository.get_by_id(order_id, tenant_id)
        if not order:
            return None
        
        order_dict = order.model_dump()
        
        # Get process instances for this order
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.process_service_url}/orders/{order_id}/process-instances"
                )
                if response.status_code == 200:
                    process_instances = response.json()
                    order_dict["process_instances"] = process_instances
                    
                    # Calculate task counts
                    total_tasks = 0
                    completed_tasks = 0
                    
                    for instance in process_instances:
                        total_tasks += len(instance.get("tasks", []))
                        # Get task details to count completed ones
                        task_response = await client.get(
                            f"{self.process_service_url}/process-instances/{instance['id']}/task-instances"
                        )
                        if task_response.status_code == 200:
                            tasks = task_response.json()
                            completed_tasks += len([t for t in tasks if t["status"] == "completed"])
                    
                    order_dict["total_tasks"] = total_tasks
                    order_dict["completed_tasks"] = completed_tasks
                    
                    # Update order in database with current counts
                    await self.repository.update(
                        order_id,
                        tenant_id,
                        {
                            "total_tasks": total_tasks,
                            "completed_tasks": completed_tasks
                        }
                    )
        except Exception as e:
            print(f"Failed to get process instances: {e}")
            order_dict["process_instances"] = []
        
        return order_dict
    
    async def update_order_progress(self, order_id: str, tenant_id: str) -> Optional[OrderResponse]:
        """Update order progress based on task completion."""
        order_dict = await self.get_order_with_processes(order_id, tenant_id)
        if not order_dict:
            return None
        
        # Determine order status based on task progress
        total_tasks = order_dict.get("total_tasks", 0)
        completed_tasks = order_dict.get("completed_tasks", 0)
        
        if total_tasks == 0:
            status = "pending"
        elif completed_tasks == 0:
            status = "in_progress"
        elif completed_tasks == total_tasks:
            status = "completed"
        else:
            status = "in_progress"
        
        # Update order status
        updated_order = await self.repository.update(
            order_id,
            tenant_id,
            {"status": status}
        )
        
        return OrderResponse(**updated_order.model_dump()) if updated_order else None
