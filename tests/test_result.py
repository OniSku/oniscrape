import orjson
from pydantic import BaseModel

from oniscrape.result import ScrapeResult


class SampleProduct(BaseModel):
    id: str
    title: str
    price: float


def test_scrape_result_to_dict_and_json(tmp_path):
    items = [
        SampleProduct(id="1", title="Keyboard", price=99.9),
        SampleProduct(id="2", title="Mouse", price=49.5),
    ]
    res = ScrapeResult(
        url="https://example.com/products",
        status_code=200,
        response_time_ms=150.25,
        items=items,
    )

    # 1. to_dict()
    data = res.to_dict()
    assert data["url"] == "https://example.com/products"
    assert data["status_code"] == 200
    assert data["items_count"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Keyboard"

    # 2. save_json()
    json_path = tmp_path / "output.json"
    res.save_json(json_path)
    assert json_path.exists()
    loaded = orjson.loads(json_path.read_bytes())
    assert loaded["items_count"] == 2

    # 3. append_ndjson()
    ndjson_path = tmp_path / "stream.ndjson"
    res.append_ndjson(ndjson_path)
    res.append_ndjson(ndjson_path)
    lines = ndjson_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4
    first_item = orjson.loads(lines[0])
    assert first_item["id"] == "1"
