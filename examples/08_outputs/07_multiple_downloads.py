from func_to_web import run
from func_to_web.types import FileResponse

def generate_reports():
    return [
        FileResponse(data=b"Report A content", filename="report_a.txt"),
        FileResponse(data=b"Report B content", filename="report_b.txt"),
        FileResponse(data=b"Report C content", filename="report_c.txt"),
    ]

run(generate_reports)
