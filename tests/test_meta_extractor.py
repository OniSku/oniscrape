from oniscrape.extractors.meta import extract_meta_relay, extract_meta_tokens


def test_extract_meta_relay():
    html = """
    <html>
    <body>
        <script type="application/json" data-sjs>
        {"require":[["RelayPrefetchedStreamCache","next",[],[{"result":{"data":{"user":{"id":"999","name":"Sam"}}}},"user_query_1"]]]}
        </script>
        <script type="application/json" data-sjs>
        {"other":"data"}
        </script>
    </body>
    </html>
    """
    relays = extract_meta_relay(html)
    assert len(relays) == 1
    assert "require" in relays[0]
    payload = relays[0]["require"][0][3][0]["result"]["data"]["user"]
    assert payload["id"] == "999"
    assert payload["name"] == "Sam"


def test_extract_meta_tokens():
    html = """
    <html>
    <head>
        <script>
        ["LSD",[],{"token":"AVr_lsd_token_123"}];
        ["SiteData",[],{"app_id":"238260118697367"}];
        ["DTSGInitialData",[],{"token":"AQ_dtsg_token_456"}];
        </script>
    </head>
    </html>
    """
    tokens = extract_meta_tokens(html)
    assert tokens["lsd"] == "AVr_lsd_token_123"
    assert tokens["app_id"] == "238260118697367"
    assert tokens["fb_dtsg"] == "AQ_dtsg_token_456"
