from types import SimpleNamespace
from app.state import move

def test_valid_workflow():
    r=SimpleNamespace(status="IDEA_CREATED")
    for s in ["SCRIPT_GENERATED","ASSETS_READY","RENDERING","RENDERED","QUALITY_CHECKING","AWAITING_APPROVAL","APPROVED","SCHEDULED","PUBLISHING","PROCESSING","PUBLISHED"]: move(r,s)
    assert r.status=="PUBLISHED"

def test_invalid_transition():
    r=SimpleNamespace(status="IDEA_CREATED")
    try: move(r,"PUBLISHED"); assert False
    except ValueError: assert True

