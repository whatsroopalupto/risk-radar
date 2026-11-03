from app.pipeline.vessel_features import assess_activity,fuse_activity

def test_baseline_and_current_coverage_are_both_required():
    assert assess_activity([10]*5,2,1,10,True)["anomaly"] is None
    for fresh,coverage,current in ((False,1,2),(True,0.5,2),(True,1,0)):
        assert assess_activity([10]*10,current,coverage,10,fresh)["anomaly"] is None

def test_corroboration_is_bounded_and_requires_news():
    features=assess_activity([10]*10,2,1,10,True)
    assert features["anomaly"]["fraction"]==0.8
    assert fuse_activity(0,0,features)==0
    assert 60<fuse_activity(60,0.6,features)<=64
    assert fuse_activity(60,0.6,{"status":"collecting","anomaly":None})==60
