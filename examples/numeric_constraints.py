from func_to_web import Annotated, Field, run


def calculate_bmi(
    age: Annotated[int, Field(ge=0, le=120)],
    weight_kg: Annotated[float, Field(ge=20, le=300)],
    height_m: Annotated[float, Field(ge=0.5, le=2.5)]
):
    """Calculate BMI with validated ranges"""
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
        "age": age,
        "bmi": round(bmi, 2),
        "category": category
    }

run(calculate_bmi)