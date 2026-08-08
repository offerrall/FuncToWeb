import copy
import json
import re
from html.parser import HTMLParser

import pytest

from func_to_web import WebFunction
from func_to_web.templates.page import (
    _titled,
    labelled_plan,
    page_from_plan,
)

VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})

OPTIONAL_END_TAGS = frozenset({"html", "head", "body", "p", "li", "option"})

PLACEHOLDERS = (
    "PLAN_JSON", "HIDDEN_JSON", "__TITLE__", "__THEME__", "__META__",
    "__DESCRIPTION__",
)

SCRIPT_TAG = re.compile(r"<script\b")


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


def node_with_id(document, element_id):
    for node in document.nodes:
        if node[1].get("id") == element_id:
            return node

    return None


def node_with_class(document, name):
    for node in document.nodes:
        if name in classes_of(node[1]):
            return node

    return None


def nodes_named(document, tag):
    return [node for node in document.nodes if node[0] == tag]


def ids_of(document):
    return [mapping["id"] for _, mapping, _ in document.nodes if "id" in mapping]


def inside_theme_root(node):
    return any("pth-root" in classes_of(mapping) for _, mapping in node[2])


def embedded_json(html, element_id):
    start = html.index(f'id="{element_id}"')
    opening = html.index(">", start) + 1
    closing = html.index("</script>", opening)
    return json.loads(html[opening:closing])


@pytest.fixture
def plan(scalar):
    return WebFunction(scalar).plan


def test_generated_page_has_no_mismatched_tags(plan):
    assert parsed(page_from_plan(plan, name="demo")).mismatched == []


def test_generated_page_leaves_only_optional_tags_open(plan):
    document = parsed(page_from_plan(plan, name="demo", description="d"))
    left = {name for name, _ in document.open_tags}

    assert left <= OPTIONAL_END_TAGS


def test_title_is_escaped(plan):
    html = page_from_plan(plan, name='<b>&"x"')

    assert "<title>&lt;b&gt;&amp;&quot;x&quot;</title>" in html
    assert "<b>" not in html


def test_title_appears_in_the_heading_too(plan):
    html = page_from_plan(plan, name="my_func")

    assert "<title>My func</title>" in html
    assert "<h1>My func</h1>" in html


def test_description_is_escaped_in_the_meta_tag(plan):
    html = page_from_plan(plan, name="demo", description='a & b <i> "q"')

    assert ('<meta name="description" '
            'content="a &amp; b &lt;i&gt; &quot;q&quot;">') in html


def test_description_is_escaped_in_the_body(plan):
    html = page_from_plan(plan, name="demo", description='a & b <i> "q"')

    assert "<p>a &amp; b &lt;i&gt; &quot;q&quot;</p>" in html
    assert "<i>" not in html


def test_empty_description_renders_no_meta_and_no_paragraph(plan):
    html = page_from_plan(plan, name="demo")

    assert 'name="description"' not in html
    assert "<p>" not in html


def test_no_placeholder_survives_rendering(plan):
    html = page_from_plan(plan, name="demo", description="d", hidden=["a"],
                          theme="dark")

    for placeholder in PLACEHOLDERS:
        assert placeholder not in html


def test_script_close_inside_plan_data_does_not_break_the_document():
    def evil(note: str = "</script><script>alert(1)</script>") -> str:
        """Injects."""
        return note

    html = WebFunction(evil).html

    assert SCRIPT_TAG.findall(html) == ["<script"] * 4
    assert "<script>" not in html
    assert "alert(1)</script>" not in html


def test_script_close_inside_plan_data_keeps_the_plan_recoverable(
    plan_of_page,
):
    payload = "</script><script>alert(1)</script>"

    def evil(note: str = payload) -> str:
        """Injects."""
        return note

    recovered = plan_of_page(WebFunction(evil).html)

    assert recovered["fields"][0]["default"] == payload


def test_script_close_inside_plan_data_keeps_the_document_valid():
    def evil(note: str = "</script><script>alert(1)</script>") -> str:
        """Injects."""
        return note

    document = parsed(WebFunction(evil).html)

    assert document.mismatched == []
    assert len(nodes_named(document, "script")) == 4


def test_markup_characters_in_the_plan_are_escaped_but_recoverable():
    html = page_from_plan({"raw": '<&>"\'', "text": "ñ日本"}, name="demo")

    assert "<&>" not in html
    assert embedded_json(html, "functoweb-plan") == {
        "raw": '<&>"\'',
        "text": "ñ日本",
        "name": "demo",
        "description": None,
    }


def test_unicode_survives_in_title_and_description(plan):
    html = page_from_plan(plan, name="año_ñ_日本", description="descripción ñ")

    assert "<title>Año ñ 日本</title>" in html
    assert "<p>descripción ñ</p>" in html


def test_plan_is_recoverable_with_the_shared_extractor(plan, plan_of_page):
    embedded = plan_of_page(page_from_plan(plan, name="demo"))

    assert embedded == {**plan, "name": "demo", "description": None}


def test_the_embedded_plan_carries_the_metadata_of_the_page(plan):
    html = page_from_plan(plan, name="Account signup",
                          description="Create an account")
    embedded = embedded_json(html, "functoweb-plan")

    assert embedded["name"] == "Account signup"
    assert embedded["description"] == "Create an account"


def test_labelling_the_plan_leaves_the_original_untouched(plan):
    before = dict(plan)

    labelled_plan(plan, name="other", description="text")

    assert plan == before


def test_hidden_names_are_recoverable(plan):
    html = page_from_plan(plan, name="demo", hidden=["b", "a"])

    assert embedded_json(html, "functoweb-hidden") == ["a", "b"]


def test_hidden_defaults_to_an_empty_list(plan):
    html = page_from_plan(plan, name="demo")

    assert embedded_json(html, "functoweb-hidden") == []


def test_stylesheets_use_relative_static_paths(plan):
    document = parsed(page_from_plan(plan, name="demo"))
    sheets = [mapping["href"] for _, mapping, _ in document.nodes
              if mapping.get("rel") == "stylesheet"]

    assert sheets == ["../static/widgets.css", "../static/page.css"]


def test_widgets_stylesheet_comes_before_the_page_stylesheet(plan):
    html = page_from_plan(plan, name="demo")

    assert html.index("widgets.css") < html.index("page.css")


def test_page_script_uses_a_relative_static_path(plan):
    document = parsed(page_from_plan(plan, name="demo"))
    sources = [mapping["src"] for _, mapping, _ in nodes_named(document,
                                                               "script")
               if "src" in mapping]

    assert sources == ["../static/page.js"]


def test_no_asset_path_is_absolute_or_remote(plan):
    document = parsed(page_from_plan(plan, name="demo"))

    for _, mapping, _ in document.nodes:
        for key in ("href", "src"):
            value = mapping.get(key)

            if value is not None:
                assert value.startswith("../")


def test_page_script_is_a_module(plan):
    document = parsed(page_from_plan(plan, name="demo"))
    module = [mapping for _, mapping, _ in nodes_named(document, "script")
              if "src" in mapping]

    assert module[0]["type"] == "module"


def test_embedded_scripts_declare_json(plan):
    document = parsed(page_from_plan(plan, name="demo"))
    embedded = [mapping for _, mapping, _ in nodes_named(document, "script")
                if "id" in mapping]

    assert [mapping["type"] for mapping in embedded] == ["application/json"] * 3


def test_fields_container_is_present(plan):
    assert node_with_id(parsed(page_from_plan(plan, name="demo")),
                        "fields") is not None


def test_submit_button_is_present(plan):
    node = node_with_id(parsed(page_from_plan(plan, name="demo")), "submit")

    assert node is not None
    assert node[0] == "button"
    assert node[1]["type"] == "button"


def test_result_container_is_present(plan):
    assert node_with_id(parsed(page_from_plan(plan, name="demo")),
                        "result") is not None


def test_upload_modal_is_present(plan):
    document = parsed(page_from_plan(plan, name="demo"))
    modal = node_with_class(document, "ftw-upload")
    dialog = node_with_class(document, "ftw-upload-dialog")

    assert modal is not None
    assert "hidden" in modal[1]
    assert dialog[1]["role"] == "dialog"
    assert dialog[1]["aria-modal"] == "true"


def test_upload_modal_labels_its_dialog(plan):
    document = parsed(page_from_plan(plan, name="demo"))
    dialog = node_with_class(document, "ftw-upload-dialog")

    assert node_with_id(document, dialog[1]["aria-labelledby"]) is not None


def test_ids_are_unique(plan):
    identifiers = ids_of(parsed(page_from_plan(plan, name="demo")))

    assert len(identifiers) == len(set(identifiers))


def test_form_elements_live_inside_the_theme_root(plan):
    document = parsed(page_from_plan(plan, name="demo"))

    for element_id in ("fields", "submit", "result"):
        assert inside_theme_root(node_with_id(document, element_id))


def test_upload_modal_lives_inside_the_theme_root(plan):
    document = parsed(page_from_plan(plan, name="demo"))

    assert inside_theme_root(node_with_class(document, "ftw-upload"))


def test_theme_root_is_the_body(plan):
    document = parsed(page_from_plan(plan, name="demo"))

    assert node_with_class(document, "pth-root")[0] == "body"


def test_system_theme_leaves_the_root_bare(plan, html_root):
    assert html_root(page_from_plan(plan, name="demo")) == "<html>"


def test_explicit_theme_marks_the_root(plan, html_root):
    root = html_root(page_from_plan(plan, name="demo", theme="dark"))

    assert root == '<html data-pth-theme="dark">'


def test_page_is_deterministic_for_the_same_plan(plan):
    first = page_from_plan(plan, name="demo", description="d", hidden=["a"])
    second = page_from_plan(plan, name="demo", description="d", hidden=["a"])

    assert first == second


def test_page_does_not_mutate_the_plan(plan):
    before = copy.deepcopy(plan)

    page_from_plan(plan, name="demo", description="d", hidden=["a"],
                   theme="dark")

    assert plan == before


def test_page_does_not_mutate_the_hidden_names(plan):
    names = ["b", "a"]

    page_from_plan(plan, name="demo", hidden=names)

    assert names == ["b", "a"]


def test_titled_turns_underscores_into_spaces():
    assert _titled("my_func") == "My func"


def test_titled_capitalises_only_the_first_letter():
    assert _titled("send_EMAIL_now") == "Send EMAIL now"


def test_titled_leaves_an_already_capitalised_name_alone():
    assert _titled("ABC") == "ABC"


def test_titled_collapses_repeated_separators():
    assert _titled("a__b   c") == "A b c"


def test_titled_strips_the_edges():
    assert _titled("_report_") == "Report"


def test_titled_accepts_an_empty_name():
    assert _titled("") == ""


def test_titled_keeps_unicode():
    assert _titled("año_ñ") == "Año ñ"
