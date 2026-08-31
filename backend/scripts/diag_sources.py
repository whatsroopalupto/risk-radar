"""Standalone local reachability probe; failures are expected to be non-fatal."""
from app.connectors.rss import RSSConnector
from app.connectors.gdelt import GDELTConnector
if __name__ == "__main__":
    for connector in (RSSConnector(),GDELTConnector()): print(connector.name,len(connector.fetch(24)))
