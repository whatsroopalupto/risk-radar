"""Non-fatal Brent corroboration connector."""
import logging
from .base import BaseConnector
LOGGER = logging.getLogger(__name__)
class PriceConnector(BaseConnector):
    name = "prices"
    def fetch(self, window_hours: int) -> list:
        """Price data is consumed separately; no canonical news signals are fabricated."""
        return []
    def percent_change_24h(self) -> float | None:
        """Fetch BZ=F movement or return None so callers can reweight honestly."""
        try:
            import yfinance as yf
            history = yf.Ticker("BZ=F").history(period="2d")
            if len(history) < 2: return None
            return float((history["Close"].iloc[-1]/history["Close"].iloc[-2]-1)*100)
        except (ImportError, ValueError, KeyError, OSError) as exc: LOGGER.warning("Brent unavailable: %s", exc); return None
