from app.render import find_font

def test_font_resolves():
    assert find_font().endswith("DejaVuSans-Bold.ttf")
