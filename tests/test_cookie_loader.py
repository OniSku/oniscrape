import orjson

from oniscrape.client import ScraperClient
from oniscrape.cookies.loader import load_cookies_from_file


def test_load_cookies_from_cookie_editor_json(tmp_path):
    cookie_data = [
        {"name": "sessionid", "value": "secret_session_123"},
        {"name": "ds_user_id", "value": "999888"},
    ]
    file_path = tmp_path / "cookies.json"
    file_path.write_bytes(orjson.dumps(cookie_data))

    cookies = load_cookies_from_file(file_path)
    assert cookies["sessionid"] == "secret_session_123"
    assert cookies["ds_user_id"] == "999888"


def test_load_cookies_from_netscape_text(tmp_path):
    text_content = """# Netscape HTTP Cookie File
.threads.net\tTRUE\t/\tTRUE\t1799999999\tsessionid\tnetscape_session_456
.threads.net\tTRUE\t/\tTRUE\t1799999999\tcsrftoken\tcsrf_val_789
"""
    file_path = tmp_path / "cookies.txt"
    file_path.write_text(text_content, encoding="utf-8")

    cookies = load_cookies_from_file(file_path)
    assert cookies["sessionid"] == "netscape_session_456"
    assert cookies["csrftoken"] == "csrf_val_789"


def test_scraper_client_from_cookies_file(tmp_path):
    dict_data = {"auth_token": "bearer_abc", "user_id": "u42"}
    file_path = tmp_path / "auth.json"
    file_path.write_bytes(orjson.dumps(dict_data))

    client = ScraperClient.from_cookies_file(str(file_path))
    assert client.cookie_storage is not None
