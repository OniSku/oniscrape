from oniscrape.extractors.generic import extract_json_ld
from oniscrape.extractors.nuxt import extract_nuxt_data


def test_extract_json_ld():
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Keyboard",
            "offers": {"@type": "Offer", "price": "49.99"}
        }
        </script>
    </head>
    </html>
    """
    data = extract_json_ld(html)
    assert len(data) == 1
    assert data[0]["name"] == "Keyboard"
    assert data[0]["offers"]["price"] == "49.99"


def test_extract_nuxt_3():
    html = """
    <html>
    <body>
        <script id="__NUXT_DATA__" type="application/json">
        [{"state":1},"ok"]
        </script>
    </body>
    </html>
    """
    data = extract_nuxt_data(html)
    assert isinstance(data, list)
    assert data[0]["state"] == 1
