import re
from typing import Any

import orjson
from selectolax.lexbor import LexborHTMLParser


def extract_json_ld(html: str) -> list[dict[str, Any]]:
    """Извлекает структурированную микроразметку Schema.org (application/ld+json)."""
    parser = LexborHTMLParser(html)
    results: list[dict[str, Any]] = []

    for script in parser.css('script[type="application/ld+json"]'):
        text = script.text()
        if not text:
            continue
        try:
            parsed = orjson.loads(text.strip())
            if isinstance(parsed, list):
                results.extend(parsed)
            elif isinstance(parsed, dict):
                results.append(parsed)
        except Exception:
            continue

    return results


def extract_json_scripts(html: str, id_pattern: str | None = None) -> list[dict[str, Any]]:
    """Извлекает содержимое всех тегов <script type="application/json">,
    опционально фильтруя по регулярному выражению для id.
    """
    parser = LexborHTMLParser(html)
    results: list[dict[str, Any]] = []

    for script in parser.css('script[type="application/json"]'):
        script_id = script.attributes.get("id") or ""
        if id_pattern and not re.search(id_pattern, script_id):
            continue

        text = script.text()
        if not text:
            continue
        try:
            parsed = orjson.loads(text.strip())
            results.append(parsed)
        except Exception:
            continue

    return results
