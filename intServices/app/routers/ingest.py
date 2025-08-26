from fastapi import APIRouter, Depends, HTTPException, Body, Query
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
    # 1) Log order as READY
    order_client = OrderClient()
    try:
        external_id = canonical.get("externalId") or payload.get("externalId") or ""
        order_created = await order_client.create_order(external_id=external_id, source="OSM", payload=canonical)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order Service error: {e}")
    # 2) Proceed with rules orchestration; include DB order id for downstream correlation
    try:
        canonical["order_id"] = order_created.get("_id") or order_created.get("id") or order_created.get("order_id")
    except Exception:
        pass
    
    # 3) Call rules
    client = RulesClient()
    try:
        result = await client.create_order(canonical, orchestrate=orchestrate, split_jobs=split_jobs, auto_schedule=auto_schedule)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Rules API error: {e}")
    return {"status": "accepted", "order": order_created, "rules_response": result, "canonical": canonical}

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
    client = RulesClient()
    try:
        result = await client.create_order(canonical, orchestrate=orchestrate, split_jobs=split_jobs, auto_schedule=auto_schedule)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Rules API error: {e}")
    return {"status": "accepted", "rules_response": result, "canonical": canonical}
