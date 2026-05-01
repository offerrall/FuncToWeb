import pandas as pd
from func_to_web import run

def sales_report():
    return pd.DataFrame({
        "product": ["Laptop", "Mouse", "Keyboard", "Monitor"],
        "units":   [12, 230, 87, 19],
        "revenue": [14400, 4600, 6960, 5700],
    })

run(sales_report)
