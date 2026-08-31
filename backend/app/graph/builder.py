"""Load and validate the intentionally small NetworkX supply graph."""
import json
from pathlib import Path
import networkx as nx
SEED_PATH = Path(__file__).with_name("seed.json")
def load_seed(path: Path = SEED_PATH) -> dict:
    """Load curated Phase 1 data and reject invalid dependency accounting."""
    seed=json.loads(path.read_text())
    for refinery in seed["refineries"]:
        total=sum(refinery["route_dependency"].values())
        if abs(total-1.0)>1e-9: raise ValueError(f"route dependencies for {refinery['id']} sum to {total}, not 1.0")
    return seed
def build_graph(seed: dict | None = None) -> nx.DiGraph:
    """Create a compact directed graph suitable for transparent local traversal."""
    seed=seed or load_seed(); graph=nx.DiGraph()
    for route in seed["routes"]: graph.add_node(route["id"],type="route",**route)
    for supplier in seed["suppliers"]:
        ident=supplier.lower().replace(" ","_"); graph.add_node(ident,type="supplier",name=supplier)
        for route in seed["routes"]: graph.add_edge(ident,route["id"])
    for port in seed["ports"]: graph.add_node(port.lower().replace(" ","_"),type="port",name=port)
    for refinery in seed["refineries"]:
        graph.add_node(refinery["id"],type="refinery",**refinery); graph.add_edge(refinery["port_id"],refinery["id"])
        for route in refinery["route_dependency"]: graph.add_edge(route,refinery["port_id"])
    return graph
