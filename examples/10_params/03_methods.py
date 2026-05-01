from func_to_web import run, Params
from func_to_web.types import Email

class UserData(Params):
    name:  str
    email: Email

    @property
    def display(self):
        return f"{self.name} <{self.email}>"

def show(data: UserData):
    return f"User: {data.display}"

run(show)
