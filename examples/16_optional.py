from func_to_web import run, Annotated, Field, Literal
from func_to_web.types import Color, Email, ImageFile, OptionalEnabled, OptionalDisabled
from datetime import date, time

def create_user(
    # Required field (no default)
    username: str,
    
    # Optional fields WITHOUT defaults
    surname: str | None,  # Auto: disabled (no default)
    age: int | OptionalDisabled,  # Explicit: always starts disabled
    favorite_color: Color | OptionalEnabled,  # Explicit: enabled without default
    birth_date: date | None,  # Auto: disabled (no default)
    language: Literal['English', 'Spanish', 'French'] | None,  # Auto: disabled (no default)
    date_of_meeting: time | OptionalEnabled,  # Explicit: enabled without default
    profile_picture: ImageFile | OptionalDisabled,  # Explicit: disabled
    
    # Optional fields WITH defaults
    job: str | None = "Dev",  # Auto: enabled (has default)
    email: Email | OptionalEnabled = "test@gmail.com",  # Explicit: always starts enabled with default
    bio: Annotated[str, Field(max_length=500, min_length=10)] | OptionalDisabled = "Software developer",  # Disabled despite having default
):

    result = f"Username: {username}"
    
    if surname:
        result += f", Surname: {surname}"
    if job:
        result += f", Job: {job}"
    if age:
        result += f", Age: {age}"
    if email:
        result += f", Email: {email}"
    if bio:
        result += f", Bio: {bio}"
    if favorite_color:
        result += f", Favorite Color: {favorite_color}"
    if birth_date:
        result += f", Birth Date: {birth_date}"
    if language:
        result += f", Language: {language}"
    if date_of_meeting:
        result += f", Date of Meeting: {date_of_meeting}"
    if profile_picture:
        result += f", Profile Picture: {profile_picture}"
    
    return result

run(create_user)