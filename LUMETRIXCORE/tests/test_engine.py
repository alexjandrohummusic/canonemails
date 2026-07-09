import os
from app.core import campaign

DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _read(fn):
    return open(os.path.join(DATA, fn), encoding="utf-8").read()

def test_generate_produces_blocks():
    with open(os.path.join(DATA, "sample_sales.csv"), "rb") as f:
        content = f.read()
    res = campaign.generate(content, "sample_sales.csv",
        _read("catalogo.PLANTILLA.json"), _read("afinidad.txt"), _read("config.txt"),
        suppression=set(), claude_token="", forced_mode="auto")
    assert "blocks" in res, res
    assert len(res["blocks"]) >= 3
    for b in res["blocks"]:
        assert b["type"] in ("tsl", "crosssell")
        assert b["asunto"]
