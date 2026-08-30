import re
from typing import Any

import orjson
from selectolax.lexbor import LexborHTMLParser


def extract_nuxt_data(html: str) -> dict[str, Any] | list[Any]:
    """Извлекает состояние Nuxt 3 (__NUXT_DATA__) или Nuxt 2 (window.__NUXT__).

    Raises:
        ValueError: Если данные Nuxt не найдены.
    """
    parser = LexborHTMLParser(html)

    # 1. Nuxt 3 JSON-массив данных
    script_node = parser.css_first("script#__NUXT_DATA__")
    if script_node and script_node.text():
        return orjson.loads(script_node.text().strip())

    # 2. Nuxt 2 window.__NUXT__ JS-объект
    match = re.search(r"window\.__NUXT__\s*=\s*(\{.*?\});", html, re.DOTALL)
    if match:
        try:
            return orjson.loads(match.group(1))
        except Exception:
            pass

    raise ValueError("Nuxt state (__NUXT_DATA__ / window.__NUXT__) not found in HTML")
