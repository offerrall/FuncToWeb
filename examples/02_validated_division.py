from func_to_web import Annotated, Field, run


def safe_divide(
    numerator: int,
    denominator: Annotated[int, Field(ge=1)]
):
    """Division that prevents divide by zero"""
    return numerator / denominator

run(safe_divide)