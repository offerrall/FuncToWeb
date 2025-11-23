from func_to_web import Annotated, Field, run


def safe_divide(
    numerator: float,
    denominator: Annotated[float, Field(gt=0)] = 1.0 # Prevent division by zero, and set default to 1.0 (All parameters allowed defaults values)
):
    """Division that prevents divide by zero"""
    return numerator / denominator # Safe from division by zero due to validation

run(safe_divide)