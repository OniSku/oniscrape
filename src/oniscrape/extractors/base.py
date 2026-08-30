from selectolax.lexbor import LexborHTMLParser


def get_html_parser(html: str) -> LexborHTMLParser:
    """Создает парсер LexborHTMLParser для быстрого поиска по дереву элементов."""
    return LexborHTMLParser(html)
