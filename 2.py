from FuncToWeb import run, Annotated, Field 

def dividir(a: int, b: Annotated[int, Field(ge=1)]):
    return a / b

run(dividir)