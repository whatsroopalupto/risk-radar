"""Small JSON logging setup for inspectable local runs."""
import logging
import sys

def configure_logging() -> None:
    """Configure a consistent console logger for every layer."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}')
