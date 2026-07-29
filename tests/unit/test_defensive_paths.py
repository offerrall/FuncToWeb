import sys
from pathlib import Path

import pytest

import func_to_web.web.router as router_module
from func_to_web import WebFunction, page_of
from func_to_web.web.print_capture import PrintCapture, install
from func_to_web.web.references import segment_of, stored_of


def add(a: int = 1) -> str:
    """Adds."""
    return str(a)


@pytest.mark.parametrize("value", [None, add, "add", 3, WebFunction])
def test_page_of_refuses_anything_but_a_web_function(value):
    with pytest.raises(TypeError, match="web_function must be WebFunction"):
        page_of(value)


def test_nested_sync_captures_restore_the_outer_one():
    outer = PrintCapture()
    inner = PrintCapture()

    with outer.capture_sync():
        print("outer first")

        with inner.capture_sync():
            print("inner only")

        print("outer again")

    assert "".join(inner.drain()) == "inner only\n"
    assert "".join(outer.drain()) == "outer first\nouter again\n"


def test_the_installed_stdout_delegates_unknown_attributes():
    install()

    assert sys.stdout.encoding == sys.stdout._original.encoding
    assert sys.stdout.isatty() == sys.stdout._original.isatty()

    with pytest.raises(AttributeError):
        sys.stdout.this_attribute_does_not_exist


def test_a_path_the_system_cannot_resolve_is_not_a_stored_file(monkeypatch,
                                                               tmp_path):
    resolve = Path.resolve

    def refuse(self, *args, **kwargs):
        if self.name == "a.txt":
            raise OSError(22, "Invalid argument")

        return resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", refuse)

    with pytest.raises(ValueError, match="is not a usable path"):
        stored_of("a.txt", tmp_path)


def test_an_unresolvable_static_name_is_not_served(monkeypatch):
    def refuse(self, *args, **kwargs):
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr(Path, "resolve", refuse)

    assert router_module.static_asset("page.js") is None


def test_the_last_shape_rule_is_unreachable_from_the_earlier_ones():
    # segment_of ends with a Path() check that no accepted string can fail:
    # separators, colons, control characters and reserved names are already
    # refused above it. It stays as the last line of defence, so this test
    # states why coverage never reaches it instead of pretending it does.
    for reference in ("a.txt", "a" * 200, ".hidden", "a-b_c.tar.gz"):
        assert segment_of(reference) == reference
        assert Path(reference).name == reference
        assert not Path(reference).is_absolute()
