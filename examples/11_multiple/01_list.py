from func_to_web import run

def calculate_bmi(weight_kg: float, height_m: float):
    """Calculate Body Mass Index"""
    return f"BMI: {weight_kg / (height_m ** 2):.2f}"

def celsius_to_fahrenheit(celsius: float):
    """Convert Celsius to Fahrenheit"""
    return f"{celsius}C = {(celsius * 9/5) + 32}F"

run([calculate_bmi, celsius_to_fahrenheit])
