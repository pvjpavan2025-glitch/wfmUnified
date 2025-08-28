from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Timestamped(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(index=True, unique=True)
    base_url: Optional[str] = None
    auth_type: Optional[str] = Field(default="none", description="none|api_key|oauth2|basic|jwt")
    is_active: bool = True

class ApplicationEndpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="application.id")
    name: str
    path: str
    method: str = Field(default="POST")
    mapping_name: Optional[str] = Field(default=None, description="Name of mapper/adapter to use")
    description: Optional[str] = None
