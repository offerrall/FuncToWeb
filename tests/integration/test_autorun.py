"""A page opened to be run instead of filled in.

autorun is the third of the parameters an opening carries —beside prefill and
hidden— and the only one that changes nothing about the document: the form,
the fields and the plan are what they would be without it. What it says is
what the page does once it is ready.
"""

import json

import pytest

from func_to_web import WebFunction, page_of


def add(a: int = 1, b: int = 2) -> int:
    """Add two numbers."""
    return a + b


def needs(a: int, b: int = 2) -> int:
    """Needs a value nobody gave."""
    return a + b


def autorun_of(html):
    start = html.index('id="functoweb-autorun"')
    opening = html.index(">", start) + 1
    closing = html.index("</script>", opening)

    return json.loads(html[opening:closing])


def hidden_of(html):
    start = html.index('id="functoweb-hidden"')
    opening = html.index(">", start) + 1
    closing = html.index("</script>", opening)

    return json.loads(html[opening:closing])


@pytest.fixture
def client(client_factory):
    return client_factory([add, needs])


def test_a_page_says_it_does_not_autorun_by_default():
    assert autorun_of(WebFunction(add).html) is False


def test_page_of_without_autorun_is_the_base_page():
    web_function = WebFunction(add)

    assert page_of(web_function) is web_function.html
    assert page_of(web_function, autorun=False) is web_function.html


def test_page_of_with_autorun_says_so():
    assert autorun_of(page_of(WebFunction(add), autorun=True)) is True


def test_autorun_rejects_anything_that_is_not_a_bool():
    for value in (1, "true", [], None):
        with pytest.raises(TypeError, match="autorun must be bool"):
            page_of(WebFunction(add), autorun=value)


def test_autorun_travels_beside_prefill_and_hidden():
    html = page_of(WebFunction(add), prefill={"a": 41}, hidden=["a"],
                   autorun=True)

    assert autorun_of(html) is True
    assert hidden_of(html) == ["a"]
    assert '"default": 41' in html


def test_the_route_does_not_autorun_when_nothing_asks(client):
    assert autorun_of(client.get("/add/").text) is False


@pytest.mark.parametrize("value", ("1", "true", "True", "yes", "on"))
def test_the_route_autoruns_when_the_query_asks(client, value):
    response = client.get("/add/", params={"autorun": value})

    assert response.status_code == 200
    assert autorun_of(response.text) is True


@pytest.mark.parametrize("value", ("0", "false", "off", "no"))
def test_the_route_does_not_autorun_when_the_query_says_not_to(client, value):
    assert autorun_of(client.get("/add/", params={"autorun": value}).text
                      ) is False


def test_the_route_refuses_a_value_that_is_not_a_boolean(client):
    assert client.get("/add/", params={"autorun": "banana"}).status_code == 422


def test_the_query_combines_with_prefill_and_hidden(client):
    response = client.get("/add/", params={
        "prefill": json.dumps({"a": 41}),
        "hidden": json.dumps(["a"]),
        "autorun": "1",
    })

    assert response.status_code == 200
    assert autorun_of(response.text) is True
    assert hidden_of(response.text) == ["a"]


def test_autorun_changes_nothing_else_about_the_page(client):
    plain = client.get("/add/").text
    running = client.get("/add/", params={"autorun": "1"}).text

    assert running != plain
    assert running.replace("functoweb-autorun\" type=\"application/json\">true",
                           "functoweb-autorun\" type=\"application/json\">false"
                           ) == plain


def test_a_form_that_cannot_be_completed_is_still_served_with_autorun(client):
    # Whether it can run is the page's business, not the route's: a required
    # field nobody filled is a page that will not press its own button.
    response = client.get("/needs/", params={"autorun": "1"})

    assert response.status_code == 200
    assert autorun_of(response.text) is True
