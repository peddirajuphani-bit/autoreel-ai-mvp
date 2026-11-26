from types import SimpleNamespace
import httpx
from app.providers import MockContentProvider, GeminiContentProvider, normalize_plan

class P: pass

def profile():
    return SimpleNamespace(brand_name="IBaseIT", primary_genre="AI + Career",
        target_audience="Indian IT professionals", country="India", language="English",
        tone="Professional", objective="Grow followers", preferred_duration=30,
        topics_include="", topics_exclude="")

def gemini_payload(data):
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json_dumps(data)}]}}]})

def json_dumps(d):
    import json
    return json.dumps(d)

def test_normalize_plan_scales_durations():
    data = {"topic": "t", "hook": "h", "title": "T", "script": "", "caption": "c",
            "hashtags": "#a", "cover_text": "x", "cta": "y", "quality_score": 120,
            "scenes": [["A", "va", 10], ["B", "vb", 10], ["C", "vc", 10]]}
    plan = normalize_plan(data, 30)
    assert plan["quality_score"] == 100
    assert sum(s[2] for s in plan["scenes"]) == 30
    assert all(isinstance(s, tuple) and len(s) == 3 for s in plan["scenes"])
    assert plan["script"] == "va vb vc"

def test_normalize_plan_accepts_dict_scenes():
    data = {"topic": "t", "hook": "h", "title": "T", "caption": "c", "quality_score": "55.5",
            "scenes": [{"headline": "A", "voiceover_text": "va", "duration": 2},
                       {"headline": "B", "voiceover_text": "vb", "duration": 6}]}
    plan = normalize_plan(data, 10)
    assert plan["quality_score"] == 55.5
    assert sum(s[2] for s in plan["scenes"]) == 10

def test_normalize_plan_rejects_bad_input():
    for bad in [None, [], {"scenes": []}, {"scenes": [["", "v", 2]]}, {"scenes": [[1, 2]]}]:
        try: normalize_plan(bad, 30)
        except ValueError: pass
        else: assert False, f"should reject {bad}"

def test_gemini_provider_parses_and_normalizes(monkeypatch):
    data = {"topic": "t", "hook": "h", "title": "T", "caption": "c", "quality_score": 90,
            "scenes": [["A", "va", 4], ["B", "vb", 4], ["C", "vc", 4], ["D", "vd", 4],
                       ["E", "ve", 4], ["F", "vf", 5], ["G", "vg", 5]]}
    def fake_post(self, url, **kw): return gemini_payload(data)
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    class FakeClient:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def post(self, *a, **kw): return fake_post(self, *a, **kw)
    monkeypatch.setattr(httpx, "Client", FakeClient)
    plan = GeminiContentProvider("k", "m").generate(profile())
    assert plan["quality_score"] == 90
    assert len(plan["scenes"]) == 7

def test_gemini_provider_maps_api_errors(monkeypatch):
    class FakeClient:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def post(self, *a, **kw): return httpx.Response(429, json={})
    monkeypatch.setattr(httpx, "Client", FakeClient)
    try: GeminiContentProvider("k", "m").generate(profile())
    except ValueError as e: assert "rate limit" in str(e).lower()
    else: assert False
