import pandas as pd
from func_to_web import run
from func_to_web.types import DataFile

def analyze_csv(file: DataFile):
    df = pd.read_csv(file)
    summary = {
        "rows":    len(df),
        "columns": len(df.columns),
        "names":   ", ".join(df.columns),
    }
    return (str(summary), df.head(20))

run(analyze_csv)
