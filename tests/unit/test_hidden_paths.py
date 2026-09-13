"""Visibility paths resolve against the same plan served to the browser."""
import json
from dataclasses import dataclass
from typing import Annotated

import pytest

from func_to_web import OpenForm, ReturnContractError
from func_to_web.models.functions import functions_of


@dataclass
class Config:
    token: str
    name: str = "Demo"


@dataclass
class Other:
    code: int


def edit(config: Config, items: list[list[Config | None]], choice: Config | Other):
    return config.token


@pytest.mark.parametrize("path", [
    "config", "config.token", "items", "items.*", "items.*.*", "items.*.*.token",
    "choice.token", "choice.code",
])
def test_open_form_accepts_nested_visibility(path):
    def opening() -> Annotated[dict, OpenForm(edit, hidden=(path,))]:
        return {}

    space = functions_of([opening, edit])
    assert space.forms["opening"].hidden == (path,)


@pytest.mark.parametrize("path", [
    "token", "config.nope", "config.", "config..token", "config.token.extra",
    "items.token", "items.*.token", "items.0.0.token", "items.*.*.nope",
    "items.*.*.", "choice.nope", "choice.$value.token", "",
])
def test_open_form_rejects_unresolved_visibility(path):
    def opening() -> Annotated[dict, OpenForm(edit, hidden=(path,))]:
        return {}

    with pytest.raises(ReturnContractError, match="unknown hidden field"):
        functions_of([opening, edit])


def test_nested_prefill_and_hidden_survive_http_opening(client_factory, plan_of_page):
    def save(config: Config) -> str:
        return config.token + ":" + config.name

    client = client_factory([save])
    values = {"config": {"token": "abc", "name": "Demo"}}
    response = client.get("/save/", params={
        "prefill": json.dumps(values), "hidden": json.dumps(["config.token"]),
    })
    assert response.status_code == 200
    assert plan_of_page(response.text)["fields"][0]["default"] == values["config"]
    assert '["config.token"]' in response.text
    invoked = client.post("/save/invoke", json=values)
    assert invoked.status_code == 200
    assert "abc:Demo" in invoked.text
