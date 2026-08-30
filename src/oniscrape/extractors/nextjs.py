import re
from typing import Any

import orjson
from selectolax.lexbor import LexborHTMLParser


def extract_next_data(html: str) -> dict[str, Any]:
    """Извлекает и парсит JSON-состояние __NEXT_DATA__ из Next.js страницы.

    Raises:
        ValueError: Если тег __NEXT_DATA__ отсутствует или поврежден.
    """
    parser = LexborHTMLParser(html)
    script_node = parser.css_first("script#__NEXT_DATA__")
    if not script_node or not script_node.text():
        raise ValueError("Next.js state (__NEXT_DATA__) not found in HTML")

    text = script_node.text().strip()
    return orjson.loads(text)


def parse_flight_line(line: str) -> tuple[str, str, Any] | None:
    """Разбирает одну строку React Flight wire-протокола вида:
    - '0:[\"$\",\"$L1\",null,{...}]'
    - '1:I[\"module.js\",[\"default\"],\"\"]'
    - '2:\"some string\"'
    - '3:HL[\"...\",...]'
    """
    line = line.strip()
    if not line or ":" not in line:
        return None

    colon_idx = line.find(":")
    row_id = line[:colon_idx].strip()
    remainder = line[colon_idx + 1 :].strip()

    if not remainder:
        return None

    # Проверяем, есть ли префикс тега типа I (Import), M (Module), H (Hint)
    tag = "J"  # default JSON payload
    first_char = remainder[0]

    if first_char.isalpha() and len(remainder) > 1 and remainder[1] in ':[{"':
        tag = first_char
        payload_str = remainder[1:]
    else:
        payload_str = remainder

    try:
        payload = orjson.loads(payload_str)
        return row_id, tag, payload
    except Exception:
        # Если это чистая строка или сложный сегмент
        return row_id, tag, payload_str


def extract_rsc_flight(html: str) -> dict[str, Any]:
    """Извлекает и декодирует потоковые чанки React Server Components (RSC Flight)
    из тегов `self.__next_f.push` в Next.js App Router (React 19).

    Возвращает словарь вида `{'rowId_tag': payload}`.
    """
    # Ищем все вызовы self.__next_f.push([..., "..."])
    matches = re.findall(
        r'self\.__next_f\.push\(\[\s*\d+\s*,\s*(".*?(?<!\\)")\s*\]\)',
        html,
        re.DOTALL,
    )

    if not matches:
        # Альтернативный паттерн без обрамляющих кавычек внутри
        matches = re.findall(
            r'self\.__next_f\.push\(\[.*?,\s*"(.*?)"\]\)',
            html,
            re.DOTALL,
        )

    full_flight_text = ""
    for match in matches:
        try:
            # Декодируем экранированную JS-строку
            decoded = orjson.loads(match if match.startswith('"') else f'"{match}"')
            full_flight_text += decoded
        except Exception:
            try:
                decoded = match.encode("utf-8").decode("unicode_escape")
                full_flight_text += decoded
            except Exception:
                full_flight_text += match

    state_tree: dict[str, Any] = {}
    for line in full_flight_text.splitlines():
        parsed = parse_flight_line(line)
        if parsed:
            row_id, tag, payload = parsed
            state_tree[f"{row_id}_{tag}"] = payload

    return state_tree


def find_rsc_payload(
    flight_tree: dict[str, Any],
    target_key: str | None = None,
) -> Any:
    """Рекурсивно ищет объекты данных / пропсов в дереве React 19 RSC Flight.

    Args:
        flight_tree: Распарсенное дерево слотов от `extract_rsc_flight`.
        target_key: Опциональный ключ поиска (например, 'posts', 'products', 'initialData').
                    Если не задан, возвращает список всех содержательных словарей данных.

    Returns:
        Найденное значение или список совпадений.
    """
    matches: list[Any] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if target_key:
                if target_key in node:
                    matches.append(node[target_key])
            else:
                # Если ищем общие данные, берем не пустые словари без служебных react-тегов
                if len(node) > 1 and not (len(node) == 1 and "$" in node):
                    matches.append(node)

            for v in node.values():
                _walk(v)

        elif isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)

    for slot_payload in flight_tree.values():
        _walk(slot_payload)

    if target_key:
        if len(matches) == 1:
            return matches[0]
        return matches if matches else None

    return matches
