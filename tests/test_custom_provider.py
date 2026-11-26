from types import SimpleNamespace
import json
import httpx
from app.providers import OpenAICompatibleContentProvider

def profile():
    return SimpleNamespace(brand_name="IBaseIT", primary_genre="AI + Career",
        target_audience="Indian IT professionals", country="India", language="English",
        tone="Professional", objective="Grow followers", preferred_duration=30,
        topics_include="", topics_exclude="")

PLAN = {"topic": "t", "hook": "h", "title": "T", "caption": "c", "quality_score": 90,
        "scenes": [["A", "va", 4], ["B", "vb", 4], ["C", "vc", 4], ["D", "vd", 4],
                   ["E", "ve", 4], ["F", "vf", 5], ["G", "vg", 5]]}

class FakeResponse:
    def __init__(self, status, body):
        self.status_code, self._body = status, body
    def json(self):
        return self._body

class FakeClient:
    status, body = 200, {"choices": [{"message": {"content": json.dumps(PLAN)}}]}
    def __init__(self, **kw): self.kw = kw
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def post(self, url, headers=None, json=None):
        self.last_url, self.last_headers, self.last_json = url, headers, json
        return FakeResponse(self.status, self.body)

def test_custom_provider_happy_path(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeClient)
    plan = OpenAICompatibleContentProvider("http://myai:1234/v1/", "mymodel").generate(profile())
    assert plan["quality_score"] == 90
    assert len(plan["scenes"]) == 7 and sum(s[2] for s in plan["scenes"]) == 30

def test_custom_provider_no_auth_header_without_key(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
    OpenAICompatibleContentProvider("http://myai:1234/v1", "mymodel").generate(profile())
    assert "Authorization" not in fake.last_headers
    assert fake.last_url == "http://myai:1234/v1/chat/completions"

def test_custom_provider_sends_bearer_and_json_mode(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
    OpenAICompatibleContentProvider("http://myai:1234/v1", "mymodel", "sekrit", True).generate(profile())
    assert fake.last_headers["Authorization"] == "Bearer sekrit"
    assert fake.last_json["response_format"] == {"type": "json_object"}

def test_custom_provider_error_mapping(monkeypatch):
    for status, expected in [(401, "credentials"), (403, "credentials"), (429, "rate limit"), (404, "endpoint")]:
        fake = FakeClient(); fake.status = status; fake.body = {}
        monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
        try: OpenAICompatibleContentProvider("http://x/v1", "m").generate(profile())
        except ValueError as e: assert expected in str(e).lower(), (status, str(e))
        else: assert False, f"should fail for {status}"

def test_custom_provider_non_json_content(monkeypatch):
    fake = FakeClient(); fake.body = {"choices": [{"message": {"content": "not json"}}]}
    monkeypatch.setattr(httpx, "Client", lambda **kw: fake)
    try: OpenAICompatibleContentProvider("http://x/v1", "m").generate(profile())
    except ValueError as e: assert "non-json" in str(e).lower()
    else: assert False
