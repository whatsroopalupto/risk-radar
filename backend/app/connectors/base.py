"""Connector protocol ensures source failures stay at the boundary."""
from abc import ABC, abstractmethod
from ..schemas import Signal
class BaseConnector(ABC):
    name: str
    @abstractmethod
    def fetch(self, window_hours: int) -> list[Signal]:
        """Fetch canonical signals; implementations return empty lists on failure."""
