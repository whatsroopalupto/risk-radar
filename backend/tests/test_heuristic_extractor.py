from .test_normalize import s
from app.pipeline.extractors.heuristic import HeuristicExtractor
def test_blockade(): assert HeuristicExtractor().extract([s("a","Iran closes the Strait of Hormuz to oil tankers")])[0].event_type=="blockade_or_closure"
def test_attack(): assert HeuristicExtractor().extract([s("a","Missile attacked oil tanker in Hormuz")])[0].event_type=="attack_on_vessel"
def test_sanctions(): assert HeuristicExtractor().extract([s("a","Iran oil sanctions tighten")])[0].event_type=="sanctions"
def test_speculative(): assert HeuristicExtractor().extract([s("a","Iran may close Hormuz oil tanker route")])[0].is_speculative
