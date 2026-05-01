from func_to_web import run
from func_to_web.types import (
    File, ImageFile, VideoFile, AudioFile,
    DataFile, TextFile, DocumentFile,
)

def upload_all(
    photo:    ImageFile,
    clip:     VideoFile,
    song:     AudioFile,
    dataset:  DataFile,
    notes:    TextFile,
    report:   DocumentFile,
    anything: File,
):
    return "All files received"

run(upload_all)
