from app.mappers.osm import OSMMapper

def test_osm_mapper_transforms_sample():
    payload = {
        "externalId": "EXT123",
        "category": "FiberInstallation",
        "serviceOrderItem": [
            {"id": "1", "action": "add", "service": {"id": "SVC1"}}
        ],
    }
    canonical = OSMMapper().to_rules(payload)
    assert "serviceOrderItems" in canonical
    assert isinstance(canonical["serviceOrderItems"], list)
