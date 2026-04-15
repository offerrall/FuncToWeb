from io import BytesIO
from pypdf import PdfWriter
from func_to_web import run
from func_to_web.types import DocumentFile, FileResponse

def merge_pdfs(files: list[DocumentFile]):
    """Upload PDFs and get a single merged file back."""
    merger = PdfWriter()
    for pdf in files:
        merger.append(pdf)

    output = BytesIO()
    merger.write(output)
    
    return FileResponse(data=output.getvalue(), filename="merged.pdf")

run(merge_pdfs)