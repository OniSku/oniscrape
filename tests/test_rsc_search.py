from oniscrape.extractors.nextjs import extract_rsc_flight, find_rsc_payload


def test_find_rsc_payload_by_key():
    html = r"""
    <html>
    <body>
        <script>
        self.__next_f.push([1, "1:I[\"/chunks/app.js\",[\"App\"],\"\"]\n0:[\"$\",\"div\",null,{\"catalog\":{\"products\":[{\"id\":\"p100\",\"name\":\"Laptop\"}]}}]\n"])
        </script>
    </body>
    </html>
    """
    flight_tree = extract_rsc_flight(html)

    # 1. Поиск по ключу "products"
    products = find_rsc_payload(flight_tree, target_key="products")
    assert isinstance(products, list)
    assert products[0]["id"] == "p100"
    assert products[0]["name"] == "Laptop"

    # 2. Поиск по ключу "catalog"
    catalog = find_rsc_payload(flight_tree, target_key="catalog")
    assert isinstance(catalog, dict)
    assert "products" in catalog
