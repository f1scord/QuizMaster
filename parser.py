# parser module — reads pdf, docx and txt files
# uses regex to extract file extension (1 pt)

import re

from exceptions import FileNotSupportedError

# set of supported extensions
SUPPORTED = {".pdf", ".docx", ".txt"}


def parse_file(path: str) -> str:
    """read any supported file and return plain text"""
    ext = _extract_ext(path)
    if ext not in SUPPORTED:
        raise FileNotSupportedError(f"unsupported file type: {ext}")
    # dispatch to correct reader based on extension
    readers = {
        ".pdf": read_pdf,
        ".docx": read_docx,
        ".txt": read_text,
    }
    return readers[ext](path)


def _extract_ext(path: str) -> str:
    # regex to get file extension like .pdf or .docx
    match = re.search(r"\.[A-Za-z0-9]+$", path)
    if not match:
        raise FileNotSupportedError("file has no extension")
    return match.group(0).lower()


def read_pdf(path: str) -> str:
    try:
        import pdfplumber
    except ModuleNotFoundError:
        raise FileNotSupportedError(
            "pdfplumber not installed. run: pip install pdfplumber"
        )
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n\n".join(parts)


def read_docx(path: str) -> str:
    try:
        import docx
    except ModuleNotFoundError:
        raise FileNotSupportedError(
            "python-docx not installed. run: pip install python-docx"
        )
    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def read_text(path: str) -> str:
    # simple text file reading with context manager
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
