from .test_normalize import s
from app.pipeline.relevance import is_relevant
def test_geo_only(): assert not is_relevant(s("a","Iran tensions"))
def test_commodity_only(): assert not is_relevant(s("a","oil market"))
def test_both(): assert is_relevant(s("a","Iran oil tanker"))
def test_neither(): assert not is_relevant(s("a","football match"))
