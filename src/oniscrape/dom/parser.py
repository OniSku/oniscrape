from selectolax.lexbor import LexborHTMLParser, LexborNode


def parse_html(html: str) -> LexborHTMLParser:
    """Создает парсер дерева DOM на базе высокопроизводительного C-движка Lexbor."""
    return LexborHTMLParser(html)


def css_text(
    context: LexborHTMLParser | LexborNode, selector: str, default: str = "", strip: bool = True
) -> str:
    """Извлекает текстовое содержимое первого найденного по селектору элемента."""
    node = context.css_first(selector)
    if not node or not node.text():
        return default
    text = node.text()
    return text.strip() if strip else text


def css_all_text(
    context: LexborHTMLParser | LexborNode, selector: str, strip: bool = True
) -> list[str]:
    """Извлекает список строк из всех найденных по селектору элементов."""
    nodes = context.css(selector)
    result: list[str] = []
    for node in nodes:
        t = node.text()
        if t:
            result.append(t.strip() if strip else t)
    return result


def css_attr(
    context: LexborHTMLParser | LexborNode, selector: str, attr: str, default: str = ""
) -> str:
    """Извлекает значение атрибута первого найденного элемента."""
    node = context.css_first(selector)
    if not node:
        return default
    val = node.attributes.get(attr)
    return val if val is not None else default


def css_all_attr(context: LexborHTMLParser | LexborNode, selector: str, attr: str) -> list[str]:
    """Извлекает список значений атрибута для всех найденных элементов."""
    nodes = context.css(selector)
    result: list[str] = []
    for node in nodes:
        val = node.attributes.get(attr)
        if val is not None:
            result.append(val)
    return result
