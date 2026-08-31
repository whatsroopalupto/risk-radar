"""Extraction boundary between prose and typed risk facts."""
from abc import ABC, abstractmethod
from ...schemas import RiskExtraction, Signal
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, signals: list[Signal]) -> list[RiskExtraction]:
        """Extract one ordered typed fact object per supplied signal."""
