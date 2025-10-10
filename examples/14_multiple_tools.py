from typing import Annotated

from pydantic import Field

from func_to_web import run


def calculate_bmi(
    weight_kg: Annotated[float, Field(ge=20, le=300)],
    height_m: Annotated[float, Field(ge=0.5, le=2.5)]
):
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return {
        "bmi": round(bmi, 2),
        "category": category
    }


def celsius_to_fahrenheit(celsius: float = 0.0):
    fahrenheit = (celsius * 9/5) + 32
    return f"{celsius}°C = {fahrenheit}°F"


def reverse_text(text: str = "Hello World"):
    return text[::-1]


def divide_numbers(
    numerator: float,
    denominator: Annotated[int, Field(ge=1)]
):
    return numerator / denominator

def greet(name: str = "User"):
    return f"Hello, {name}!"

# Run multiple tools on one server
run([calculate_bmi, celsius_to_fahrenheit, reverse_text, divide_numbers, greet])