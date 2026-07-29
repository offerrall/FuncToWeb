import re
from html.parser import HTMLParser

import pytest

from func_to_web import WebFunction, WebFunctions
from func_to_web.templates.index import index_of

VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})

OPTIONAL_END_TAGS = frozenset({"html", "head", "body", "p", "li", "option"})

PLACEHOLDERS = ("__ITEMS__", "__PREFIX__", "__TITLE__", "__THEME__")

INTERNAL_ROUTES = ("/invoke", "invoke-stream", "/upload", "/returns")

ANCHOR = re.compile(r'<a href="#([^"]*)" data-slug="([^"]*)">(.*?)</a>')


class Document(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.open_tags = []
        self.nodes = []
        self.mismatched = []

    def handle_starttag(self, tag, attrs):
        mapping = dict(attrs)
        self.nodes.append((tag, mapping, tuple(self.open_tags)))

        if tag not in VOID_TAGS:
            self.open_tags.append((tag, mapping))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

        if tag not in VOID_TAGS:
            self.open_tags.pop()

    def handle_endtag(self, tag):
        names = [name for name, _ in self.open_tags]

        if tag not in names:
            self.mismatched.append(tag)
            return

        while self.open_tags[-1][0] != tag:
            closed = self.open_tags.pop()[0]

            if closed not in OPTIONAL_END_TAGS:
                self.mismatched.append(closed)

        self.open_tags.pop()


def parsed(html):
    document = Document()
    document.feed(html)
    document.close()
    return document


def classes_of(mapping):
    return set((mapping.get("class") or "").split())


def anchors_of(html):
    return [(mapping.get("href"), mapping.get("data-slug"),
             classes_of(mapping))
            for tag, mapping, _ in parsed(html).nodes if tag == "a"]


def function_anchors(html):
    return [entry for entry in anchors_of(html) if entry[1] is not None]


def doc_anchor(html):
    for entry in anchors_of(html):
        if "doc" in entry[2]:
            return entry

    return None


def space_of_functions(*fns, title="Space"):
    return WebFunctions(tuple(WebFunction(fn) for fn in fns), title=title)


@pytest.fixture
def alpha():
    def alpha_one(a: int = 1) -> str:
        """First tool."""
        return "a"

    return alpha_one


@pytest.fixture
def beta():
    def beta_two(b: int = 1) -> str:
        """Second tool."""
        return "b"

    return beta_two


@pytest.fixture
def bare():
    def bare_tool(c: int = 1) -> str:
        return "c"

    return bare_tool


def test_title_is_escaped(alpha):
    html = index_of(space_of_functions(alpha, title='<b>&"x"'), "")

    assert "<title>&lt;b&gt;&amp;&quot;x&quot;</title>" in html
    assert "<b>" not in html


def test_title_heads_the_navigation(alpha):
    html = index_of(space_of_functions(alpha, title="My space"), "")

    assert "<h1>My space</h1>" in html


def test_a_single_function_is_listed(alpha):
    html = index_of(space_of_functions(alpha), "")

    assert [entry[1] for entry in function_anchors(html)] == ["alpha-one"]


def test_several_functions_are_listed(alpha, beta, bare):
    html = index_of(space_of_functions(alpha, beta, bare), "")

    assert [entry[1] for entry in function_anchors(html)] == [
        "alpha-one", "beta-two", "bare-tool",
    ]


def test_functions_keep_the_space_order(alpha, beta):
    html = index_of(space_of_functions(beta, alpha), "")

    assert [entry[1] for entry in function_anchors(html)] == [
        "beta-two", "alpha-one",
    ]


def test_every_function_appears_once(alpha, beta):
    html = index_of(space_of_functions(alpha, beta), "")
    slugs = [entry[1] for entry in function_anchors(html)]

    assert len(slugs) == len(set(slugs))


def test_names_get_the_title_touch_up(alpha, beta):
    html = index_of(space_of_functions(alpha, beta), "")

    assert "<strong>Alpha one</strong>" in html
    assert "<strong>Beta two</strong>" in html


def test_descriptions_are_rendered(alpha, beta):
    html = index_of(space_of_functions(alpha, beta), "")

    assert "<span>First tool.</span>" in html
    assert "<span>Second tool.</span>" in html


def test_descriptions_are_escaped():
    def risky(a: int = 1) -> str:
        """A & B <i> "q"."""
        return "x"

    html = index_of(space_of_functions(risky), "")

    assert "<span>A &amp; B &lt;i&gt; &quot;q&quot;.</span>" in html
    assert "<i>" not in html


def test_function_without_description_has_no_span(bare):
    html = index_of(space_of_functions(bare), "")
    entry = ANCHOR.search(html)

    assert entry.group(2) == "bare-tool"
    assert "<span>" not in entry.group(3)


def test_function_links_are_relative_fragments(alpha, beta):
    html = index_of(space_of_functions(alpha, beta), "/tools")

    for href, slug, _ in function_anchors(html):
        assert href == f"#{slug}"


def test_function_links_ignore_the_prefix(alpha):
    without = function_anchors(index_of(space_of_functions(alpha), ""))
    with_prefix = function_anchors(index_of(space_of_functions(alpha),
                                            "/tools"))

    assert [entry[0] for entry in without] == [entry[0]
                                               for entry in with_prefix]


def test_doc_link_is_present(alpha):
    html = index_of(space_of_functions(alpha), "")

    assert doc_anchor(html) is not None
    assert "<strong>/doc</strong>" in html


def test_doc_link_uses_the_prefix(alpha):
    html = index_of(space_of_functions(alpha), "/tools")

    assert doc_anchor(html)[0] == "/tools/doc"


def test_doc_link_without_prefix(alpha):
    html = index_of(space_of_functions(alpha), "")

    assert doc_anchor(html)[0] == "/doc"


def test_stylesheet_uses_the_prefix(alpha):
    html = index_of(space_of_functions(alpha), "/tools")

    assert 'href="/tools/static/widgets.css"' in html


def test_frame_source_uses_the_prefix(alpha):
    html = index_of(space_of_functions(alpha), "/tools")

    assert "`/tools/${link.dataset.slug}/`" in html


def test_no_placeholder_survives_rendering(alpha):
    html = index_of(space_of_functions(alpha), "/tools", "dark")

    for placeholder in PLACEHOLDERS:
        assert placeholder not in html


def test_system_theme_leaves_the_root_bare(alpha, html_root):
    assert html_root(index_of(space_of_functions(alpha), "")) == "<html>"


def test_explicit_theme_marks_the_root(alpha, html_root):
    root = html_root(index_of(space_of_functions(alpha), "", "dark"))

    assert root == '<html data-pth-theme="dark">'


def test_invalid_theme_is_refused(alpha):
    with pytest.raises(ValueError):
        index_of(space_of_functions(alpha), "", "neon")


def test_html_has_no_mismatched_tags(alpha, beta):
    assert parsed(index_of(space_of_functions(alpha, beta), "")).mismatched == []


def test_html_leaves_only_optional_tags_open(alpha, beta):
    document = parsed(index_of(space_of_functions(alpha, beta), ""))
    left = {name for name, _ in document.open_tags}

    assert left <= OPTIONAL_END_TAGS


def test_ids_are_unique(alpha, beta):
    document = parsed(index_of(space_of_functions(alpha, beta), ""))
    identifiers = [mapping["id"] for _, mapping, _ in document.nodes
                   if "id" in mapping]

    assert len(identifiers) == len(set(identifiers))


def test_links_live_inside_the_theme_root(alpha):
    document = parsed(index_of(space_of_functions(alpha), ""))

    for tag, _, ancestors in document.nodes:
        if tag == "a":
            assert any("pth-root" in classes_of(mapping)
                       for _, mapping in ancestors)


def test_a_slug_with_a_quote_cannot_reach_the_template(alpha):
    with pytest.raises(ValueError):
        WebFunction(alpha, slug='a" onload="x')


def test_a_slug_with_markup_cannot_reach_the_template(alpha):
    with pytest.raises(ValueError):
        WebFunction(alpha, slug="<script>")


def test_slug_is_written_verbatim_in_both_attributes(alpha):
    html = index_of(space_of_functions(alpha), "")

    assert '<a href="#alpha-one" data-slug="alpha-one">' in html


def test_a_space_without_functions_is_impossible():
    with pytest.raises(ValueError):
        WebFunctions(())


def test_no_internal_route_is_exposed(alpha, beta):
    html = index_of(space_of_functions(alpha, beta), "/tools")

    for route in INTERNAL_ROUTES:
        assert route not in html


def test_unicode_title_and_description_survive():
    def acentuada(a: int = 1) -> str:
        """Descripción con ñ y 日本."""
        return "x"

    html = index_of(space_of_functions(acentuada, title="Título ñ"), "")

    assert "<title>Título ñ</title>" in html
    assert "<span>Descripción con ñ y 日本.</span>" in html


def test_index_is_deterministic(alpha, beta):
    space = space_of_functions(alpha, beta)

    assert index_of(space, "/tools") == index_of(space, "/tools")


def test_index_does_not_depend_on_the_space_instance(alpha, beta):
    first = index_of(space_of_functions(alpha, beta), "/tools")
    second = index_of(space_of_functions(alpha, beta), "/tools")

    assert first == second
