from func_to_web import run
from func_to_web.types import FileResponse

def make_report(title: str = "Report", lines: int = 5):
    content = f"# {title}\n\n" + "\n".join(f"- Line {i}" for i in range(lines))
    return FileResponse(data=content.encode(), filename=f"{title}.md")

run(make_report)
