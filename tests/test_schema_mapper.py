import pytest
from pydantic import BaseModel

from oniscrape.pipeline.schema_mapper import map_state_to_model


class ProductModel(BaseModel):
    id: str
    title: str
    price: float


def test_map_state_to_single_model():
    state = {"pageProps": {"product": {"id": "prod_1", "title": "Wireless Mouse", "price": 29.99}}}
    res = map_state_to_model(
        state=state,
        query="pageProps.product",
        model_cls=ProductModel,
    )
    assert isinstance(res, ProductModel)
    assert res.id == "prod_1"
    assert res.title == "Wireless Mouse"
    assert res.price == 29.99


def test_map_state_to_list_of_models_with_projection():
    state = {
        "data": {
            "items": [
                {"item_id": "1", "item_name": "Item 1", "cost": 10.5},
                {"item_id": "2", "item_name": "Item 2", "cost": 20.0},
            ]
        }
    }
    res = map_state_to_model(
        state=state,
        query="data.items[*].{id: item_id, title: item_name, price: cost}",
        model_cls=ProductModel,
    )
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0].id == "1"
    assert res[0].title == "Item 1"
    assert res[1].price == 20.0


def test_map_state_empty_result_non_strict():
    state = {"data": {"items": []}}
    res = map_state_to_model(
        state=state,
        query="data.items[*].{id: id, title: title, price: price}",
        model_cls=ProductModel,
        strict=False,
    )
    assert res == []


def test_map_state_empty_result_strict_raises():
    state = {"data": {"items": []}}
    with pytest.raises(ValueError, match="empty result in strict mode"):
        map_state_to_model(
            state=state,
            query="data.items[*].{id: id, title: title, price: price}",
            model_cls=ProductModel,
            strict=True,
        )
