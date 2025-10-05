from FuncToWeb import run

def show_lists(
    color: list[str] = ["Red", "Green", "Blue", "Yellow"],
    quantity: list[int] = [1, 5, 10, 25, 50, 100],
    price: list[float] = [9.99, 19.99, 49.99, 99.99],
    premium: list[bool] = [True, False]
):
    return f"Color: {color} ({type(color).__name__}); " \
           f"Quantity: {quantity} ({type(quantity).__name__}); " \
           f"Price: ${price} ({type(price).__name__}); " \
           f"Premium: {premium} ({type(premium).__name__})"

run(show_lists)