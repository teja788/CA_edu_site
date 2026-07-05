"""Turn uploaded .md / .txt / .pdf files into (title, body) pairs."""
import io
import re
from pathlib import Path

TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".text"}


def parse_upload(filename: str, data: bytes) -> tuple[str, str]:
    """Return (title, body) for an uploaded file. Raises ValueError on unsupported types."""
    ext = Path(filename).suffix.lower()
    if ext in TEXT_EXTENSIONS:
        body = data.decode("utf-8", errors="replace")
    elif ext == ".pdf":
        body = _pdf_text(data)
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Use .md, .txt or .pdf.")
    return _title_from(filename, body), body.strip()


def _pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF import requires the 'pypdf' package (pip install pypdf).") from exc
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def _title_from(filename: str, body: str) -> str:
    # Prefer the first markdown heading, else the first non-empty line, else the filename.
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        return (heading.group(1) if heading else line)[:120]
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip() or "Untitled import"
