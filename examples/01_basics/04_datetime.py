from datetime import date, time
from func_to_web import run

def event(event_date: date = date.today(), start_time: time = time(9, 0)):
    return f"Event on {event_date} at {start_time}"

run(event)
