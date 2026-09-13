"""PDF text extraction."""

from __future__ import annotations

import io
from typing import Any

from pypdf import PdfReader


def extract_pdf_text(file_bytes: bytes) -> dict[str, Any]:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(text.strip())
    full = "\n\n".join(p for p in pages if p)
    return {
        "page_count": len(reader.pages),
        "text": full[:120_000],
        "pages": pages,
    }


def detect_brand(text: str) -> str:
    lower = text.lower()
    if "carlisle" in lower:
        return "Carlisle Homes"
    if "metricon" in lower:
        return "Metricon"
    if "builder" in lower:
        return "the builder"
    return "Unknown"
