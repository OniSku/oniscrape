import pytest

from oniscrape.client import ScraperClient
from oniscrape.config import ScraperConfig


@pytest.mark.asyncio
async def test_client_session_creation():
    client = ScraperClient(config=ScraperConfig(default_impersonate="chrome124"))

    async with client.create_session(proxy="http://127.0.0.1:8080") as session:
        assert session.impersonate == "chrome124"
        assert session.proxies == {"all": "http://127.0.0.1:8080"}
