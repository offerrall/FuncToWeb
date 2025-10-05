# FuncToWeb

**Transform any Python function into a web interface automatically.**

FuncToWeb is a minimalist library that generates web UIs from your Python functions with zero boilerplate. Just add type hints, call `run()`, and you're done.

## Installation

```bash
pip install functoweb
```

## Quick Start

The simplest example possible:

```python
from FuncToWeb import run

def dividir(a: int, b: int):
    return a / b

run(dividir)
```

That's it! Open `http://localhost:8000` and you'll see a form with two integer inputs.

## Adding Constraints

You can add constraints to your inputs using `Annotated` and `Field` from `typing` and `pydantic` respectively:

```python
from FuncToWeb import run, Annotated, Field 

def dividir(a: int, b: Annotated[int, Field(ge=1)]):
    return a / b

run(dividir)
```

Now `b` must be at least 1. The UI automatically enforces this with HTML5 validation.
