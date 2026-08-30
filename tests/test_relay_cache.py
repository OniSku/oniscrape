from oniscrape.extractors.meta import extract_relay_cache


def test_extract_relay_cache_scheduled_server_js_nested():
    """Тест реальной структуры Threads / Instagram:
    ScheduledServerJS -> __bbox -> require -> RelayPrefetchedStreamCache.
    """
    html = """
    <html>
    <body>
        <script type="application/json" data-sjs>
        {
            "require": [
                [
                    "ScheduledServerJS",
                    "handle",
                    null,
                    [
                        {
                            "__bbox": {
                                "require": [
                                    [
                                        "RelayPrefetchedStreamCache",
                                        "next",
                                        [],
                                        [
                                            "adp_BarcelonaLoggedOutFeedContainerQueryRelayPreloader_6a94474bf40f96188756930",
                                            {
                                                "__bbox": {
                                                    "result": {
                                                        "data": {
                                                            "feedData": {
                                                                "edges": [
                                                                    {"node": {"id": "post_100", "caption": "Threads live post"}}
                                                                ]
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    ]
                                ]
                            }
                        }
                    ]
                ]
            ]
        }
        </script>
    </body>
    </html>
    """
    cache = extract_relay_cache(html)
    query_key = "adp_BarcelonaLoggedOutFeedContainerQueryRelayPreloader_6a94474bf40f96188756930"
    assert query_key in cache
    feed_data = cache[query_key]
    assert "feedData" in feed_data
    assert feed_data["feedData"]["edges"][0]["node"]["caption"] == "Threads live post"


def test_extract_relay_cache_direct():
    html = """
    <html>
    <body>
        <script type="application/json" data-sjs>
        {
            "require": [
                [
                    "RelayPrefetchedStreamCache",
                    "next",
                    [],
                    [
                        "DirectQuery",
                        {
                            "result": {
                                "data": {
                                    "user": {"name": "Zuck"}
                                }
                            }
                        }
                    ]
                ]
            ]
        }
        </script>
    </body>
    </html>
    """
    cache = extract_relay_cache(html)
    assert "DirectQuery" in cache
    assert cache["DirectQuery"]["user"]["name"] == "Zuck"
