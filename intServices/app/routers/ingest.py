from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from typing import Optional
import time
from ..core.security import validate_api_key
from ..mappers.base import registry
from ..services.rules_client import RulesClient
from ..services.order_client import OrderClient

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(validate_api_key)])

@router.post("/osm")
async def ingest_osm(
    payload: dict = Body(...),
    dry_run: bool = Query(False),
    orchestrate: bool = Query(True, description="Trigger downstream job creation and scheduling via rules-service"),
    split_jobs: bool = Query(False, description="One job per service order item"),
    auto_schedule: bool = Query(True, description="Schedule jobs immediately"),
):
    try:
        mapper = registry.get("osm")
        canonical = mapper.to_rules(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid OSM payload: {e}")
    if dry_run:
        return {"status": "validated", "rules_response": None, "canonical": canonical}
    # 1) Create order with enhanced metadata
    order_client = OrderClient()
    try:
        external_id = canonical.get("externalId") or payload.get("externalId") or ""
        priority = canonical.get("priority", "medium")
        description = canonical.get("description", f"OSM Order {external_id}")
        customer_id = canonical.get("customerId") or canonical.get("customer_id")
        
        order_created = await order_client.create_order(
            external_id=external_id, 
            source="OSM", 
            payload=canonical,
            priority=priority,
            description=description,
            customer_id=customer_id
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")
    # 2) Proceed with rules orchestration; include DB order id for downstream correlation
    try:
        canonical["order_id"] = order_created.get("_id") or order_created.get("id") or order_created.get("order_id")
    except Exception:
        pass
    
    # 3) Evaluate rules and trigger process orchestration
    client = RulesClient()
    try:
        result = await client.evaluate_order(canonical, orchestrate=orchestrate, auto_schedule=auto_schedule)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Rules API error: {e}")
    
    return {
        "status": "accepted", 
        "order": order_created, 
        "rules_response": result, 
        "canonical": canonical,
        "processes_created": len(result.get("jobs", [])),
        "auto_scheduled": auto_schedule
    }

@router.post("/{app_code}")
async def ingest_generic(
    app_code: str,
    payload: dict = Body(...),
    dry_run: bool = Query(False),
    orchestrate: bool = Query(True),
    split_jobs: bool = Query(False),
    auto_schedule: bool = Query(True),
):
    try:
        mapper = registry.get(app_code)
        canonical = mapper.to_rules(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload for {app_code}: {e}")
    if dry_run:
        return {"status": "validated", "rules_response": None, "canonical": canonical}
    
    # Create order first
    order_client = OrderClient()
    try:
        external_id = canonical.get("externalId") or payload.get("externalId") or f"{app_code}-{int(time.time())}"
        priority = canonical.get("priority", "medium")
        description = canonical.get("description", f"{app_code.upper()} Order {external_id}")
        customer_id = canonical.get("customerId") or canonical.get("customer_id")
        
        order_created = await order_client.create_order(
            external_id=external_id,
            source=app_code.upper(),
            payload=canonical,
            priority=priority,
            description=description,
            customer_id=customer_id
        )
        
        # Add order_id to canonical data for rules processing
        canonical["order_id"] = order_created.get("_id") or order_created.get("id")
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")
    
    # Evaluate rules and orchestrate processes
    client = RulesClient()
    try:
        result = await client.evaluate_order(canonical, orchestrate=orchestrate, auto_schedule=auto_schedule)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Rules API error: {e}")
    
    return {
        "status": "accepted", 
        "order": order_created,
        "rules_response": result, 
        "canonical": canonical,
        "processes_created": len(result.get("jobs", [])),
        "auto_scheduled": auto_schedule
    }


# Order monitoring endpoints
@router.get("/orders/{order_id}")
async def get_order_status(
    order_id: str = Path(..., description="Order ID")
):
    """Get order status and basic information."""
    order_client = OrderClient()
    try:
        order = await order_client.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")


@router.get("/orders/{order_id}/details")
async def get_order_details(
    order_id: str = Path(..., description="Order ID")
):
    """Get detailed order information including processes and tasks."""
    order_client = OrderClient()
    try:
        order_details = await order_client.get_order_with_processes(order_id)
        if not order_details:
            raise HTTPException(status_code=404, detail="Order not found")
        return order_details
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")


@router.post("/orders/{order_id}/refresh")
async def refresh_order_progress(
    order_id: str = Path(..., description="Order ID")
):
    """Refresh order progress by updating task completion status."""
    import httpx
    from ..core.config import settings
    
    try:
        # Call order service to refresh progress
        headers = {"Content-Type": "application/json"}
        if hasattr(settings, 'order_api_token') and settings.order_api_token:
            headers["Authorization"] = f"Bearer {settings.order_api_token}"
        
        url = f"{settings.order_api_base_url}/orders/{order_id}/refresh-progress"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers)
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="Order not found")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Order not found")
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")
