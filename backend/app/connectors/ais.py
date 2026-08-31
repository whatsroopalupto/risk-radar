"""Phase 2 AIS connector seat; deliberately contains no live vessel implementation."""
from .base import BaseConnector
from ..schemas import Signal
class AISConnector(BaseConnector):
    """Phase 2 will use aisstream.io WebSocket for Hormuz/Bab-el-Mandeb transit counts versus a 30-day baseline, anchorage dwell, and AIS-gap events."""
    name = "ais"
    def fetch(self, window_hours: int) -> list[Signal]:
        """Return no data: fabricating vessel observations would create false risk."""
        return []
