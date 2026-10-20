"""
Общие помощники тестов.
"""

from __future__ import annotations

import base64
import io

from docx import Document
from docx.oxml.ns import qn

_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def png() -> io.BytesIO:
    """
    Свежий поток с PNG 1×1 (python-docx читает поток один раз).
    """
    return io.BytesIO(_PNG)


def texts(doc: Document) -> list[str]:
    return [p.text for p in doc.paragraphs]


def instructions(doc: Document) -> list[str]:
    return [e.text.strip() for e in doc.element.body.iter(qn("w:instrText"))]
