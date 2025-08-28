from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.db import get_session
from ..repositories.app_repo import ApplicationRepository, EndpointRepository
from ..models.base import Application, ApplicationEndpoint
from ..models.schemas import ApplicationCreate, ApplicationUpdate, EndpointCreate, EndpointUpdate
from ..core.security import validate_api_key

router = APIRouter(prefix="/applications", tags=["applications"], dependencies=[Depends(validate_api_key)])

@router.get("/", response_model=List[Application])
async def list_apps(session: AsyncSession = Depends(get_session)):
    return await ApplicationRepository(session).list()

@router.post("/", response_model=Application)
async def create_app(app: ApplicationCreate, session: AsyncSession = Depends(get_session)):
    repo = ApplicationRepository(session)
    existing = await repo.get_by_code(app.code)
    if existing:
        raise HTTPException(status_code=400, detail="Application code already exists")
    return await repo.create(Application(**app.model_dump()))

@router.get("/{app_id}", response_model=Application)
async def get_app(app_id: int, session: AsyncSession = Depends(get_session)):
    app = await ApplicationRepository(session).get(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.put("/{app_id}", response_model=Application)
async def update_app(app_id: int, data: ApplicationUpdate, session: AsyncSession = Depends(get_session)):
    updated = await ApplicationRepository(session).update(app_id, data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated

@router.delete("/{app_id}")
async def delete_app(app_id: int, session: AsyncSession = Depends(get_session)):
    ok = await ApplicationRepository(session).delete(app_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"deleted": True}

# Endpoints CRUD

@router.get("/{app_id}/endpoints", response_model=List[ApplicationEndpoint])
async def list_endpoints(app_id: int, session: AsyncSession = Depends(get_session)):
    return await EndpointRepository(session).list(app_id=app_id)

@router.post("/{app_id}/endpoints", response_model=ApplicationEndpoint)
async def create_endpoint(app_id: int, ep: EndpointCreate, session: AsyncSession = Depends(get_session)):
    ep_model = ApplicationEndpoint(application_id=app_id, **ep.model_dump())
    return await EndpointRepository(session).create(ep_model)

@router.get("/endpoints/{endpoint_id}", response_model=ApplicationEndpoint)
async def get_endpoint(endpoint_id: int, session: AsyncSession = Depends(get_session)):
    ep = await EndpointRepository(session).get(endpoint_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return ep

@router.put("/endpoints/{endpoint_id}", response_model=ApplicationEndpoint)
async def update_endpoint(endpoint_id: int, data: EndpointUpdate, session: AsyncSession = Depends(get_session)):
    updated = await EndpointRepository(session).update(endpoint_id, data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return updated

@router.delete("/endpoints/{endpoint_id}")
async def delete_endpoint(endpoint_id: int, session: AsyncSession = Depends(get_session)):
    ok = await EndpointRepository(session).delete(endpoint_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return {"deleted": True}
