from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Party(BaseModel):
    id: str
    role: str
    name: Optional[str] = None

class GeoLocation(BaseModel):
    latitude: str
    longitude: str

class Place(BaseModel):
    id: Optional[str]
    role: Optional[str]
    type: Optional[str] = Field(default="GeographicAddress", alias="@type")
    street: Optional[str]
    city: Optional[str]
    postalCode: Optional[str]
    country: Optional[str]
    geographicLocation: Optional[GeoLocation]

class ServiceCharacteristic(BaseModel):
    name: str
    value: Any
    valueType: str

class ServiceSpecification(BaseModel):
    id: str
    name: Optional[str]
    version: Optional[str]

class Service(BaseModel):
    id: str
    category: Optional[str]
    serviceType: Optional[str]
    serviceSpecification: Optional[ServiceSpecification]
    serviceCharacteristic: Optional[List[ServiceCharacteristic]] = []
    place: Optional[List[Place]] = []

class ServiceOrderItem(BaseModel):
    id: str
    action: str
    service: Service

class CanonicalRulesOrder(BaseModel):
    externalId: Optional[str]
    priority: Optional[str]
    category: Optional[str]
    orderDate: Optional[str]
    requestedCompletionDate: Optional[str]
    description: Optional[str]
    relatedParty: Optional[List[Party]] = []
    serviceOrderItems: List[ServiceOrderItem]
    notes: Optional[List[Dict[str, Any]]] = []
    relationships: Optional[List[Dict[str, Any]]] = []
