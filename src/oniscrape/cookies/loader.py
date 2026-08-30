from pathlib import Path
from typing import Any

import orjson


def parse_cookie_payload(data: Any) -> dict[str, str]:
    """Разбирает различные форматы куки (список от Cookie-Editor, словарь, строки)."""
    cookies: dict[str, str] = {}

    if isinstance(data, dict):
        for k, v in data.items():
            cookies[str(k)] = str(v)
    elif isinstance(data, list):
        # Формат экспорта Cookie-Editor / EditThisCookie: [{"name": "...", "value": "..."}, ...]
        for item in data:
            if isinstance(item, dict) and "name" in item and "value" in item:
                cookies[str(item["name"])] = str(item["value"])

    return cookies


def parse_netscape_cookies(text: str) -> dict[str, str]:
    """Парсит текстовый формат Netscape cookie file (cookies.txt)."""
    cookies: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            name = parts[5]
            value = parts[6]
            cookies[name] = value
        elif len(parts) == 2:
            cookies[parts[0]] = parts[1]
    return cookies


def load_cookies_from_json(json_str: str) -> dict[str, str]:
    """Загружает куки из JSON-строки (поддерживает формат Cookie-Editor и плоский словарь)."""
    data = orjson.loads(json_str)
    return parse_cookie_payload(data)


def load_cookies_from_file(filepath: str | Path) -> dict[str, str]:
    """Загружает куки из файла (.json или .txt в формате Netscape / Cookie-Editor).

    Поддерживает:
    - JSON-файлы, экспортированные из расширений браузера (Cookie-Editor, EditThisCookie).
    - Обычные JSON-словари `{"sessionid": "...", "auth_token": "..."}`.
    - Текстовые файлы cookies.txt в формате Netscape.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Файл куки не найден: {filepath}")

    raw_bytes = path.read_bytes()

    # 1. Пробуем распарсить как JSON
    try:
        data = orjson.loads(raw_bytes)
        return parse_cookie_payload(data)
    except Exception:
        pass

    # 2. Пробуем распарсить как Netscape text
    text = raw_bytes.decode("utf-8", errors="ignore")
    return parse_netscape_cookies(text)
