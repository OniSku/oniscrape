from oniscrape.dom.parser import (
    css_all_attr,
    css_all_text,
    css_attr,
    css_text,
    parse_html,
)


def test_dom_parser_helpers():
    html = """
    <div id="container">
        <h1 class="title">  Hello World  </h1>
        <ul class="items">
            <li><a href="/item/1" class="link">First</a></li>
            <li><a href="/item/2" class="link">Second</a></li>
        </ul>
        <span class="empty"></span>
    </div>
    """
    tree = parse_html(html)

    # css_text
    assert css_text(tree, "h1.title") == "Hello World"
    assert css_text(tree, "h1.title", strip=False) == "  Hello World  "
    assert css_text(tree, ".nonexistent", default="N/A") == "N/A"
    assert css_text(tree, ".empty", default="none") == "none"

    # css_all_text
    assert css_all_text(tree, "ul.items li a") == ["First", "Second"]

    # css_attr & css_all_attr
    assert css_attr(tree, "a.link", "href") == "/item/1"
    assert css_all_attr(tree, "a.link", "href") == ["/item/1", "/item/2"]
