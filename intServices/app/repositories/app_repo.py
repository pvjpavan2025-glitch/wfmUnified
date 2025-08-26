from typing import Optional, List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.base import Application, ApplicationEndpoint

class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[Application]:
        res = await self.session.execute(select(Application))
        return list(res.scalars().all())

    async def get(self, app_id: int) -> Optional[Application]:
        return await self.session.get(Application, app_id)

    async def get_by_code(self, code: str) -> Optional[Application]:
        res = await self.session.execute(select(Application).where(Application.code==code))
        return res.scalars().first()

    async def create(self, app: Application) -> Application:
        self.session.add(app)
        await self.session.commit()
        await self.session.refresh(app)
        return app

    async def update(self, app_id: int, data: dict) -> Optional[Application]:
        app = await self.get(app_id)
        if not app:
            return None
        for k, v in data.items():
            setattr(app, k, v)
        await self.session.commit()
        await self.session.refresh(app)
        return app

    async def delete(self, app_id: int) -> bool:
        app = await self.get(app_id)
        if not app:
            return False
        await self.session.delete(app)
        await self.session.commit()
        return True

class EndpointRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, app_id: Optional[int] = None) -> List[ApplicationEndpoint]:
        stmt = select(ApplicationEndpoint)
        if app_id:
            stmt = stmt.where(ApplicationEndpoint.application_id==app_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get(self, endpoint_id: int) -> Optional[ApplicationEndpoint]:
        return await self.session.get(ApplicationEndpoint, endpoint_id)

    async def create(self, ep: ApplicationEndpoint) -> ApplicationEndpoint:
        self.session.add(ep)
        await self.session.commit()
        await self.session.refresh(ep)
        return ep

    async def update(self, endpoint_id: int, data: dict) -> Optional[ApplicationEndpoint]:
        ep = await self.get(endpoint_id)
        if not ep:
            return None
        for k, v in data.items():
            setattr(ep, k, v)
        await self.session.commit()
        await self.session.refresh(ep)
        return ep

    async def delete(self, endpoint_id: int) -> bool:
        ep = await self.get(endpoint_id)
        if not ep:
            return False
        await self.session.delete(ep)
        await self.session.commit()
        return True
