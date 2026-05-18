"""PDF text extraction."""
from __future__ import annotations

import io
import re

from pypdf import PdfReader

from app.core.exceptions import IngestionError


def extract_pages_from_pdf(data: bytes) -> list[str]:
    """Return a list of cleaned page texts (1-indexed by position)."""
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise IngestionError(f"Failed to read PDF: {exc}") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001
            text = ""
        pages.append(_clean(text))
    return pages


def _clean(text: str) -> str:
    # Normalise whitespace, strip control chars.
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
