from abc import ABC, abstractmethod
from typing import Any, Dict

class Mapper(ABC):
    @abstractmethod
    def to_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class MapperRegistry:
    def __init__(self):
        self._mappers: Dict[str, Mapper] = {}

    def register(self, name: str, mapper: Mapper):
        self._mappers[name.lower()] = mapper

    def get(self, name: str) -> Mapper:
        m = self._mappers.get(name.lower())
        if not m:
            raise KeyError(f"No mapper registered for {name}")
        return m

registry = MapperRegistry()
