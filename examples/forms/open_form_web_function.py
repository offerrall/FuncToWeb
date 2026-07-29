"""An OpenForm can name a WebFunction, and that instance is the target."""

from typing import Annotated

from func_to_web import Choices, Min, OpenForm, WebFunction, run

STOCK: dict[str, int] = {"SKU-1": 12, "SKU-2": 3, "SKU-3": 0}

Sku = Annotated[str, Choices(values=tuple(STOCK))]


def adjust_stock(sku: str, units: Annotated[int, Min(0)]) -> str:
    """Set the units in stock of an article."""
    STOCK[sku] = units

    return f"{sku} now has {units} units."


ADJUST = WebFunction(
    adjust_stock,
    name="Adjust stock",
    description="Correct the counted units of one article.",
    slug="stock-adjust",
)


def find_article(
    sku: Sku = "SKU-1",
) -> Annotated[dict, OpenForm(ADJUST, hidden=("sku",))]:
    """Open the stock editor of an article by its own slug.

    The OpenForm points at the WebFunction instance, so that very instance is
    the one the space must register.
    """
    return {"sku": sku, "units": STOCK[sku]}


def stock_report(only_empty: bool = False) -> str:
    """List the articles in stock, all of them or only the empty ones."""
    rows = [f"{sku}: {units}" for sku, units in STOCK.items()
            if units == 0 or not only_empty]

    return "\n".join(rows) if rows else "Nothing to report."


if __name__ == "__main__":
    run([find_article, ADJUST, stock_report], title="Warehouse")
