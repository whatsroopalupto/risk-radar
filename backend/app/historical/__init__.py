"""Standalone historical research utilities for scenario labelling and validation.

This package intentionally stays separate from live signal ingestion and scoring.
"""

from .validation import validate_historical_dataset

__all__ = ["validate_historical_dataset"]
