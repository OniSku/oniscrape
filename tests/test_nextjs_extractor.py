import pytest

from oniscrape.extractors.nextjs import (
    extract_next_data,
    extract_rsc_flight,
    parse_flight_line,
)


def test_extract_next_data_success():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"user":{"id":"123","username":"alex"}}},"page":"/user"}
        </script>
    </head>
    <body><h1>Profile</h1></body>
    </html>
    """
    data = extract_next_data(html)
    assert data["props"]["pageProps"]["user"]["id"] == "123"
    assert data["props"]["pageProps"]["user"]["username"] == "alex"
    assert data["page"] == "/user"


def test_extract_next_data_missing():
    html = "<html><body><h1>No next data here</h1></body></html>"
    with pytest.raises(ValueError, match="__NEXT_DATA__"):
        extract_next_data(html)


def test_parse_flight_line():
    line_json = '0:["$","$L1",null,{"title":"Hello World"}]'
    res = parse_flight_line(line_json)
    assert res is not None
    row_id, tag, payload = res
    assert row_id == "0"
    assert tag == "J"
    assert payload[3]["title"] == "Hello World"

    line_import = '1:I["/static/chunks/app.js",["default"],""]'
    res_imp = parse_flight_line(line_import)
    assert res_imp is not None
    row_id, tag, payload = res_imp
    assert row_id == "1"
    assert tag == "I"
    assert payload[0] == "/static/chunks/app.js"


def test_extract_rsc_flight_multi_chunks():
    html = r"""
    <!DOCTYPE html>
    <html>
    <body>
        <script>
        self.__next_f.push([1, "1:I[\"/chunks/feed.js\",[\"Feed\"],\"\"]\n0:[\"$\",\"main\",null,{\"posts\":[{\"id\":\"p1\",\"text\":\"first post\"}]}]\n"])
        </script>
        <script>
        self.__next_f.push([1, "2:[\"$\",\"footer\",null,{\"copyright\":\"2026\"}]\n"])
        </script>
    </body>
    </html>
    """
    flight_tree = extract_rsc_flight(html)
    assert "1_I" in flight_tree
    assert "0_J" in flight_tree
    assert "2_J" in flight_tree
    assert flight_tree["0_J"][3]["posts"][0]["id"] == "p1"
    assert flight_tree["2_J"][3]["copyright"] == "2026"
