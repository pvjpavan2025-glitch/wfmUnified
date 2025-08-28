from typing import Any, Dict, List
from .base import Mapper, registry

class OSMMapper(Mapper):
    def to_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # naive safe extraction with defaults; in production add full schema validation
        order_items: List[Dict[str, Any]] = []
        for item in payload.get("serviceOrderItem", []) or []:
            order_items.append({
                "id": item.get("id", ""),
                "action": item.get("action", "add"),
                "service": item.get("service", {}),
            })

        rules_payload = {
            "externalId": payload.get("externalId"),
            "priority": payload.get("priority"),
            "category": payload.get("category"),
            "orderDate": payload.get("orderDate"),
            "requestedCompletionDate": payload.get("requestedCompletionDate"),
            "description": payload.get("description"),
            "relatedParty": payload.get("relatedParty", []),
            "serviceOrderItems": order_items,
            "notes": payload.get("note", []),
            "relationships": payload.get("orderRelationship", []),
        }
        return rules_payload

# register
registry.register("osm", OSMMapper())
