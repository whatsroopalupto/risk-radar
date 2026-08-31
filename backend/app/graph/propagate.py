"""Explainable route-to-refinery arithmetic."""
from datetime import datetime
from ..schemas import RefineryExposure, RouteContribution, RouteRisk
from ..pipeline.scorer import band_for_score
def propagate(route_risks: list[RouteRisk], seed: dict) -> list[RefineryExposure]:
    """Apply validated dependency shares and retain every contribution for UI audit."""
    scores={route.route_id:route.composite_score for route in route_risks}; output=[]
    for refinery in seed["refineries"]:
        contributions=[RouteContribution(route_id=route,dependency_share=share,route_score=scores.get(route,0)) for route,share in refinery["route_dependency"].items()]
        exposure=sum(item.dependency_share*item.route_score for item in contributions)
        output.append(RefineryExposure(refinery_id=refinery["id"],name=refinery["name"],operator=refinery["operator"],port_id=refinery["port_id"],exposure_score=exposure,band=band_for_score(exposure),contributions=contributions))
    return output
