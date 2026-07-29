from typing import TypedDict


class DownloadOutput(TypedDict):
    type: str
    value: str
    filename: str


def download_output(reference: str, filename: str) -> DownloadOutput:
    return {
        "type": "download",
        "value": reference,
        "filename": filename,
    }
