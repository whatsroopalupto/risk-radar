"""Static Phase 1 source credibility lookup."""
from urllib.parse import urlparse
TIER_ONE = {"reuters.com","apnews.com","bloomberg.com","ft.com","wsj.com","bbc.com","bbc.co.uk","aljazeera.com","spglobal.com","argusmedia.com"}
TIER_TWO = {"thehindu.com","indianexpress.com","business-standard.com","livemint.com","economictimes.indiatimes.com","cnbc.com","theguardian.com","hellenicshippingnews.com","tradewindsnews.com"}
WEIGHTS = {1: 1.0, 2: .75, 3: .5, 4: .25}
def credibility_for_domain(domain: str | None) -> tuple[int, float]:
    """Resolve known publisher tiers while retaining an unknown-source penalty."""
    if not domain: return 4, WEIGHTS[4]
    host = urlparse(domain if "://" in domain else f"//{domain}").hostname
    if not host: return 4, WEIGHTS[4]
    host = host.lower().removeprefix("www.")
    registrable = ".".join(host.split(".")[-2:])
    if host in TIER_ONE or registrable in TIER_ONE: return 1, WEIGHTS[1]
    if host in TIER_TWO or registrable in TIER_TWO: return 2, WEIGHTS[2]
    return 3, WEIGHTS[3]
