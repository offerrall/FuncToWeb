import pytest

from func_to_web import WebFunction, page_of


def greeting(name: str = "Ana") -> str:
    """Say hello to a person."""
    return f"Hello {name}"


@pytest.mark.parametrize("hide_title,hide_description", [
    (False, False), (True, False), (False, True), (True, True),
])
def test_visibility_is_per_opening_and_keeps_the_contract(
    hide_title, hide_description, client_factory, plan_of_page,
):
    fn = WebFunction(greeting)
    original = fn.html
    options = dict(hide_title=hide_title, hide_description=hide_description)
    html = page_of(fn, **options)
    response = client_factory(fn).get("/greeting/", params={
        name: str(value).lower() for name, value in options.items()
    })

    assert response.status_code == 200
    assert response.text == html
    assert ("<h1>Greeting</h1>" in html) is (not hide_title)
    assert ("<p>Say hello to a person.</p>" in html) is (not hide_description)
    assert ("<header>" in html) is (not (hide_title and hide_description))
    assert "<title>Greeting</title>" in html
    assert plan_of_page(html) == plan_of_page(original)
    assert fn.html is original
    assert page_of(fn) is original


@pytest.mark.parametrize("option", ["hide_title", "hide_description"])
def test_visibility_rejects_non_boolean_options(option, client_factory):
    with pytest.raises(TypeError, match=f"{option} must be bool"):
        page_of(WebFunction(greeting), **{option: "true"})
    response = client_factory(greeting).get("/greeting/", params={option: "maybe"})
    assert response.status_code == 422
    assert response.json()["detail"] == f"{option} must be a boolean"


def test_visibility_combines_with_other_opening_options(client_factory, plan_of_page):
    response = client_factory(greeting).get("/greeting/", params={
        "hide_title": "1", "hide_description": "1", "autorun": "1",
        "prefill": '{"name":"Luis"}', "hidden": '["name"]',
    })
    assert response.status_code == 200
    assert "<header>" not in response.text
    assert plan_of_page(response.text)["fields"][0]["default"] == "Luis"
    assert 'id="functoweb-hidden" type="application/json">["name"]' in response.text
    assert 'id="functoweb-autorun" type="application/json">true' in response.text


def test_hiding_title_of_function_without_description_omits_header():
    def plain() -> str:
        return "done"

    assert "<header>" not in page_of(WebFunction(plain), hide_title=True)
