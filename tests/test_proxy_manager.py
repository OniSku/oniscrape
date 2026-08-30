from oniscrape.config import ProxyConfig
from oniscrape.proxy.manager import ProxyManager


def test_proxy_manager_round_robin():
    cfg = ProxyConfig(
        urls=["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"],
        strategy="round_robin",
    )
    pm = ProxyManager(cfg)

    # 3 прокси в ротации
    p1 = pm.get_proxy()
    p2 = pm.get_proxy()
    p3 = pm.get_proxy()
    p4 = pm.get_proxy()

    assert {p1, p2, p3} == {"http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"}
    assert p4 == p1


def test_proxy_manager_cooldown():
    cfg = ProxyConfig(
        urls=["http://p1:8080", "http://p2:8080"],
        max_fails_before_cooldown=1,
        cooldown_seconds=100.0,
    )
    pm = ProxyManager(cfg)

    # Репортим фейл для p1 -> должен уйти в кулдаун
    pm.report_fail("http://p1:8080")

    # Теперь доступен только p2
    assert pm.get_proxy() == "http://p2:8080"
    assert pm.get_proxy() == "http://p2:8080"
