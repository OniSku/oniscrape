import re
from typing import Any

import orjson
from selectolax.lexbor import LexborHTMLParser


def extract_meta_relay(html: str) -> list[dict[str, Any]]:
    """Извлекает все preloaded GraphQL-ответы из Relay Stream Cache
    в Threads / Instagram / Facebook.
    """
    parser = LexborHTMLParser(html)
    results: list[dict[str, Any]] = []

    for script in parser.css('script[type="application/json"][data-sjs]'):
        text = script.text()
        if not text:
            continue
        try:
            parsed = orjson.loads(text)
            if isinstance(parsed, dict) and "require" in parsed:
                results.append(parsed)
        except Exception:
            continue

    return results


def extract_relay_cache(html: str) -> dict[str, Any]:
    """Автоматически разворачивает предзагруженный Relay-кэш Threads / Instagram / Facebook.

    Распаковывает вызовы `RelayPrefetchedStreamCache` внутри `ScheduledServerJS`,
    извлекая полезную нагрузку `__bbox -> result -> data`
    в плоский словарь вида:
    `{"QueryName": { ...данные... }}`.
    """
    raw_relays = extract_meta_relay(html)
    unwrapped: dict[str, Any] = {}
    query_counter = 1

    def _process_require_list(items: Any) -> None:
        nonlocal query_counter
        if not isinstance(items, list):
            return

        for item in items:
            if not isinstance(item, list) or len(item) < 3:
                continue

            module_name = item[0]

            # 1. Прямой вызов RelayPrefetchedStreamCache
            if module_name == "RelayPrefetchedStreamCache":
                args = item[3] if len(item) > 3 else (item[2] if len(item) > 2 else [])
                if isinstance(args, list) and len(args) >= 2:
                    query_name = args[0] if isinstance(args[0], str) else f"Query_{query_counter}"
                    query_counter += 1

                    payload_info = args[1]
                    if isinstance(payload_info, dict):
                        if "__bbox" in payload_info and isinstance(payload_info["__bbox"], dict):
                            payload_info = payload_info["__bbox"]
                        if "result" in payload_info and isinstance(payload_info["result"], dict):
                            payload_info = payload_info["result"]
                        if "data" in payload_info and isinstance(payload_info["data"], dict):
                            payload_info = payload_info["data"]

                    unwrapped[query_name] = payload_info

            # 2. Вложенные контейнеры (ScheduledServerJS / Bootloader) с __bbox
            else:
                args = item[3] if len(item) > 3 else (item[2] if len(item) > 2 else [])
                if isinstance(args, list):
                    for arg in args:
                        if isinstance(arg, dict) and "__bbox" in arg:
                            bbox = arg["__bbox"]
                            if isinstance(bbox, dict) and "require" in bbox:
                                _process_require_list(bbox["require"])

    for block in raw_relays:
        _process_require_list(block.get("require", []))

    return unwrapped


def extract_meta_tokens(html: str) -> dict[str, str]:
    """Извлекает токены CSRF и идентификаторы приложения из HTML:
    - `lsd`: CSRF-токен для POST-запросов к /api/graphql
    - `app_id`: Идентификатор приложения (например, для x-ig-app-id)
    - `fb_dtsg`: Маркер безопасности Meta
    """
    lsd_match = re.search(r'\["LSD",\[\],{"token":"([^"]+)"\}', html)
    if not lsd_match:
        lsd_match = re.search(r'"LSD",\[\],\{"token":"([^"]+)"\}', html)
    if not lsd_match:
        lsd_match = re.search(r'name="lsd"\s+value="([^"]+)"', html)

    app_id_match = re.search(r'\["SiteData",\[\],{"app_id":"([^"]+)"\}', html)
    if not app_id_match:
        app_id_match = re.search(r'"app_id":"(\d+)"', html)

    dtsg_match = re.search(r'"DTSGInitialData",\[\],{"token":"([^"]+)"\}', html)

    return {
        "lsd": lsd_match.group(1) if lsd_match else "",
        "app_id": app_id_match.group(1)
        if app_id_match
        else "238260118697367",  # default threads web app id
        "fb_dtsg": dtsg_match.group(1) if dtsg_match else "",
    }
