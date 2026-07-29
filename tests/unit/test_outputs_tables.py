import sys

import pytest

from func_to_web.outputs import output_of, outputs_of, table_output


class FakeFrame:
    columns = ["a", "b"]
    values = [[1, 2]]

    def itertuples(self, index=False):
        return iter(self.values)

    def rows(self):
        return self.values


class FakeArray:
    ndim = 2
    shape = (1, 2)

    def tolist(self):
        return [[1, 2]]


def pandas_module():
    return pytest.importorskip("pandas")


def polars_module():
    return pytest.importorskip("polars")


def numpy_module():
    return pytest.importorskip("numpy")


def test_pandas_empty_frame_has_no_headers_and_no_rows():
    pandas = pandas_module()

    assert table_output(pandas.DataFrame()) == {
        "type": "table",
        "headers": [],
        "rows": [],
    }


def test_pandas_frame_with_no_rows_keeps_its_headers():
    pandas = pandas_module()

    assert table_output(pandas.DataFrame({"a": [], "b": []})) == {
        "type": "table",
        "headers": ["a", "b"],
        "rows": [],
    }


def test_pandas_single_column():
    pandas = pandas_module()

    assert table_output(pandas.DataFrame({"name": ["Ana", "Bea"]})) == {
        "type": "table",
        "headers": ["name"],
        "rows": [["Ana"], ["Bea"]],
    }


def test_pandas_several_columns_keep_their_order():
    pandas = pandas_module()
    frame = pandas.DataFrame({"name": ["Ana"], "age": [25], "city": ["Vigo"]})

    assert table_output(frame) == {
        "type": "table",
        "headers": ["name", "age", "city"],
        "rows": [["Ana", "25", "Vigo"]],
    }


def test_pandas_index_is_ignored():
    pandas = pandas_module()
    frame = pandas.DataFrame({"value": [1, 2]}, index=["first", "second"])

    assert table_output(frame) == {
        "type": "table",
        "headers": ["value"],
        "rows": [["1"], ["2"]],
    }


def test_pandas_keeps_each_column_type():
    pandas = pandas_module()
    frame = pandas.DataFrame({"count": [1200], "ratio": [0.5]})

    assert table_output(frame)["rows"] == [["1200", "0.5"]]


def test_pandas_heterogeneous_types_are_stringified():
    pandas = pandas_module()
    frame = pandas.DataFrame({"n": [1], "f": [1.5], "s": ["x"], "b": [True]})

    assert table_output(frame)["rows"] == [["1", "1.5", "x", "True"]]


def test_pandas_none_survives_in_an_object_column():
    pandas = pandas_module()
    frame = pandas.DataFrame({"value": ["x", None]}, dtype=object)

    assert table_output(frame)["rows"] == [["x"], ["None"]]


def test_pandas_nan_becomes_its_text():
    pandas = pandas_module()
    frame = pandas.DataFrame({"value": [1.5, float("nan")]})

    assert table_output(frame)["rows"] == [["1.5"], ["nan"]]


def test_pandas_non_string_column_names_become_strings():
    pandas = pandas_module()
    frame = pandas.DataFrame([[10, 20, 30]], columns=[1, None, ("a", "b")])

    assert table_output(frame)["headers"] == ["1", "None", "('a', 'b')"]


def test_polars_empty_frame_has_no_headers_and_no_rows():
    polars = polars_module()

    assert table_output(polars.DataFrame()) == {
        "type": "table",
        "headers": [],
        "rows": [],
    }


def test_polars_single_column():
    polars = polars_module()

    assert table_output(polars.DataFrame({"name": ["Ana", "Bea"]})) == {
        "type": "table",
        "headers": ["name"],
        "rows": [["Ana"], ["Bea"]],
    }


def test_polars_several_columns_keep_their_order():
    polars = polars_module()
    frame = polars.DataFrame({"name": ["Ana"], "age": [25]})

    assert table_output(frame) == {
        "type": "table",
        "headers": ["name", "age"],
        "rows": [["Ana", "25"]],
    }


def test_polars_heterogeneous_types_are_stringified():
    polars = polars_module()
    frame = polars.DataFrame({"n": [1], "f": [1.5], "s": ["x"], "b": [True]})

    assert table_output(frame)["rows"] == [["1", "1.5", "x", "True"]]


def test_numpy_two_dimensional_array_becomes_a_table():
    numpy = numpy_module()

    assert table_output(numpy.array([[1, 2], [3, 4]])) == {
        "type": "table",
        "headers": ["Column 1", "Column 2"],
        "rows": [["1", "2"], ["3", "4"]],
    }


def test_numpy_empty_two_dimensional_array_keeps_generated_headers():
    numpy = numpy_module()

    assert table_output(numpy.zeros((0, 3))) == {
        "type": "table",
        "headers": ["Column 1", "Column 2", "Column 3"],
        "rows": [],
    }


def test_numpy_single_row():
    numpy = numpy_module()

    assert table_output(numpy.array([[1, 2, 3]]))["rows"] == [["1", "2", "3"]]


def test_numpy_single_column():
    numpy = numpy_module()

    assert table_output(numpy.array([[1], [2]])) == {
        "type": "table",
        "headers": ["Column 1"],
        "rows": [["1"], ["2"]],
    }


def test_numpy_diverse_types_are_stringified():
    numpy = numpy_module()
    array = numpy.array([[1, "x"], [True, 2.5]], dtype=object)

    assert table_output(array)["rows"] == [["1", "x"], ["True", "2.5"]]


@pytest.mark.parametrize("shape", [(), (3,), (2, 2, 2)])
def test_numpy_arrays_that_are_not_two_dimensional_are_not_tables(shape):
    numpy = numpy_module()

    assert table_output(numpy.zeros(shape)) is None


@pytest.mark.parametrize("shape", [(), (3,), (2, 2, 2)])
def test_numpy_arrays_that_are_not_two_dimensional_become_text(shape):
    numpy = numpy_module()

    assert output_of(numpy.zeros(shape))["type"] == "text"


def test_table_is_detected_before_the_value_is_treated_as_a_collection():
    pandas = pandas_module()
    frame = pandas.DataFrame({"a": [1, 2]})

    assert output_of(frame) == {
        "type": "table",
        "headers": ["a"],
        "rows": [["1"], ["2"]],
    }


def test_table_inside_a_collection_stays_a_table():
    pandas = pandas_module()
    frame = pandas.DataFrame({"a": [1]})
    outputs = output_of(["before", frame, "after"])

    assert [output["type"] for output in outputs] == ["text", "table", "text"]


def test_nested_table_keeps_its_place_in_the_order():
    numpy = numpy_module()
    outputs = outputs_of([1, [numpy.array([[1, 2]]), 2]])

    assert [output["type"] for output in outputs] == ["text", "table", "text"]


def test_pandas_is_not_detected_when_the_module_is_not_imported(monkeypatch):
    pandas = pandas_module()
    frame = pandas.DataFrame({"a": [1]})

    monkeypatch.delitem(sys.modules, "pandas")

    assert table_output(frame) is None


def test_polars_is_not_detected_when_the_module_is_not_imported(monkeypatch):
    polars = polars_module()
    frame = polars.DataFrame({"a": [1]})

    monkeypatch.delitem(sys.modules, "polars")

    assert table_output(frame) is None


def test_numpy_is_not_detected_when_the_module_is_not_imported(monkeypatch):
    numpy = numpy_module()
    array = numpy.array([[1, 2]])

    monkeypatch.delitem(sys.modules, "numpy")

    assert table_output(array) is None


def test_undetected_frame_falls_back_to_text(monkeypatch):
    pandas = pandas_module()
    frame = pandas.DataFrame({"a": [1]})

    monkeypatch.delitem(sys.modules, "pandas")

    assert output_of(frame)["type"] == "text"


def test_frame_lookalike_is_not_a_table():
    assert table_output(FakeFrame()) is None


def test_array_lookalike_is_not_a_table():
    assert table_output(FakeArray()) is None


def test_frame_lookalike_becomes_text():
    assert output_of(FakeFrame())["type"] == "text"


@pytest.mark.parametrize("value", [[[1, 2]], ((1, 2),), {"a": [1]}, "text"])
def test_ordinary_values_are_never_tables(value):
    assert table_output(value) is None


def test_headers_and_cells_are_strings():
    pandas = pandas_module()
    frame = pandas.DataFrame([[10, 1.5], [20, True]], columns=[1, "b"])
    table = table_output(frame)

    assert all(type(header) is str for header in table["headers"])
    assert all(type(cell) is str for row in table["rows"] for cell in row)


def test_table_output_has_no_value_key():
    numpy = numpy_module()

    assert "value" not in table_output(numpy.array([[1]]))
