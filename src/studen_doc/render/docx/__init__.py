"""Рендер в Word (.docx)."""
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.renderer import DocxRenderer
from studen_doc.render.docx.title import render_title

__all__ = ["Context", "DocxRenderer", "render_title"]
