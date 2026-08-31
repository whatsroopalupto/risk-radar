import pytest
from app.graph.builder import load_seed
from app.graph.propagate import propagate
from app.schemas import RouteRisk
from datetime import datetime,timezone
def test_seed_loads(): assert len(load_seed()["routes"])==4
def test_shares_sum(): assert all(sum(x["route_dependency"].values())==1 for x in load_seed()["refineries"])
def test_propagation():
 seed={"refineries":[{"id":"x","name":"X","operator":"O","port_id":"p","route_dependency":{"r":1.0}}]}; route=RouteRisk(route_id="r",name="R",chokepoints=[],news_score=.5,market_score=0,composite_score=50,band="medium",contributing_signal_ids=[],computed_at=datetime.now(timezone.utc)); assert propagate([route],seed)[0].exposure_score==50
