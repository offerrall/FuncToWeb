from datetime import date
from func_to_web import run
from func_to_web.types import Color, Email, ImageFile

def all_optional(
    count: int       | None = None,
    flag:  bool      | None = None,
    tag:   str       | None = None,
    mail:  Email     | None = None,
    color: Color     | None = None,
    photo: ImageFile | None = None,
    day:   date      | None = None,
):
    return "All optional"

run(all_optional)
