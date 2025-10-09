from func_to_web import run, Email, Annotated, Field, ImageFile, Color, date, time, Literal

def create_user(
    username: str, # Required field
    surname: str | None = None, # Optional field
    job: str | None = "Dev", # Optional with default value
    age: int | None = None, # Optional, disabled by default
    email: Email | None = "test@gmail.com", # Optional email with default value
    bio: Annotated[str, Field(max_length=500, min_length=10)] | None = None, # Optional with validation
    favorite_color: Color | None = None, # Optional color picker
    birth_date: date | None = None, # Optional date picker
    language: Literal['English', 'Spanish', 'French'] | None = None, # Optional dropdown
    date_of_meeting: time | None = None, # Optional time picker
    profile_picture: Annotated[ImageFile, Field(description="Upload your profile picture")] | None = None # Optional file upload
):
    result = f"Username: {username}"
    if age:
        result += f", Age: {age}"
    if surname:
        result += f", Surname: {surname}"
    if job:
        result += f", Job: {job}"
    if email:
        result += f", Email: {email}"
    if bio:
        result += f", Bio: {bio}"
    if profile_picture:
        result += f", Profile Picture: {profile_picture.filename}"
    if favorite_color:
        result += f", Favorite Color: {favorite_color}"
    if birth_date:
        result += f", Birth Date: {birth_date}"
    if language:
        result += f", Language: {language}"
    if date_of_meeting:
        result += f", Date of Meeting: {date_of_meeting}"
    return result

run(create_user)