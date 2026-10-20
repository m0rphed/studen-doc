"""
Конвертер формул на pandoc: все формулы документа - одним запуском процесса.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from studen_doc.equations.base import MathConversionError
from studen_doc.pandoc import PandocError, find_pandoc, run_pandoc

if TYPE_CHECKING:
    from lxml import etree

__all__ = ["PandocConverter", "find_pandoc"]

_M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_PANDOC_ARGS = ("-f", "markdown+tex_math_dollars", "-t", "docx", "-o", "-")


def _one_line(latex: str) -> str:
    return latex.replace("\r", " ").replace("\n", " ").strip()


@dataclass(slots=True)
class PandocConverter:
    """
    ``MathConverter`` через pandoc.

    ``command`` - команда запуска без аргументов (``["pandoc"]``, ``["/opt/pandoc/bin/pandoc"]``, в тестах -
    ``[sys.executable, "fake_pandoc.py"]``); ``None`` - найти автоматически. Процесс запускается списком
    аргументов без оболочки, обмен - байтами UTF-8, поэтому поведение одинаково на Windows и Linux
    (см. ``studen_doc.pandoc``). Результаты кэшируются в экземпляре: повторные формулы повторно
    не конвертируются.
    """

    command: Sequence[str] | None = None
    timeout_s: float = 120.0
    _cache: dict[str, bytes] = field(default_factory=dict, init=False, repr=False)

    def convert(self, formulas: Sequence[str]) -> Mapping[str, etree._Element]:
        from lxml import etree  # лениво: импорт пакета не должен загружать lxml

        unique = list(dict.fromkeys(formulas))
        for latex in unique:
            if not latex.strip():
                raise MathConversionError("Пустая формула")
        missing = [latex for latex in unique if latex not in self._cache]
        if missing:
            self._cache.update(self._run(missing))
        return {latex: etree.fromstring(self._cache[latex]) for latex in unique}

    # ------------------------------------------------------------------------------------------
    def _run(self, formulas: list[str]) -> dict[str, bytes]:
        """
        Один процесс на все формулы: каждая - отдельный абзац ``$...$`` исходного markdown.
        """
        source = "\n\n".join(f"${_one_line(latex)}$" for latex in formulas)
        try:
            result = run_pandoc(_PANDOC_ARGS, source.encode("utf-8"), command=self.command, timeout_s=self.timeout_s)
        except PandocError as error:
            raise MathConversionError(str(error)) from error
        return self._collect(formulas, result.stdout, result.diagnostics)

    @staticmethod
    def _collect(formulas: list[str], docx: bytes, diagnostics: str) -> dict[str, bytes]:
        from lxml import etree

        with zipfile.ZipFile(io.BytesIO(docx)) as archive:
            body = etree.fromstring(archive.read("word/document.xml")).find(f"{_W}body")

        paragraphs = [] if body is None else body.findall(f"{_W}p")
        if len(paragraphs) != len(formulas):
            raise MathConversionError(
                f"pandoc вернул {len(paragraphs)} абзацев вместо {len(formulas)} (формула с пустой строкой?)"
            )
        converted: dict[str, bytes] = {}
        failed: list[str] = []

        for latex, paragraph in zip(formulas, paragraphs, strict=True):
            omath = paragraph.find(f".//{_M}oMath")
            if omath is None:  # pandoc не падает на ошибке, а оставляет формулу обычным текстом
                failed.append(latex)
            else:
                converted[latex] = etree.tostring(omath)

        if failed:
            listing = "\n".join(f"  - {latex}" for latex in failed)
            hint = f"\nСообщение pandoc: {diagnostics}" if diagnostics else ""
            raise MathConversionError(f"pandoc не смог разобрать формулы:\n{listing}{hint}")

        return converted
