from app.pipeline.credibility import credibility_for_domain
def test_tier_one(): assert credibility_for_domain("WWW.Reuters.com")[0]==1
def test_tier_two(): assert credibility_for_domain("thehindu.com")[0]==2
def test_tier_three(): assert credibility_for_domain("oilprice.com")[0]==3
def test_unknown(): assert credibility_for_domain(None)[0]==4
def test_unparseable_sentinel(): assert credibility_for_domain("unknown")[0]==4
