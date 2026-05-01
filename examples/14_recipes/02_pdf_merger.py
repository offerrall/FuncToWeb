from io import BytesIO
from pypdf import PdfWriter
from func_to_web import run
from func_to_web.types import DocumentFile, FileResponse

def merge_pdfs(files: list[DocumentFile]):
    writer = PdfWriter()
    for pdf in files:
        writer.append(pdf)
    buf = BytesIO()
    writer.write(buf)
    return FileResponse(data=buf.getvalue(), filename="merged.pdf")

run(merge_pdfs)
