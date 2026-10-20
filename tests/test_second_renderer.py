"""Доказательство расширяемости: второй формат вывода подключается без правок ядра.

Минимальный Markdown-рендерер читает тот же IR (``ResolvedReport``), что и DOCX-рендерер, и реализует
протокол ``Renderer``. Typst или LaTeX подключаются точно так же: свой пакет ``render/<формат>/``.
"""
from pathlib import Path

from helpers import png
from studen_doc import Bullets, Figure, Formula, P, Ref, Report, Subsection, Table
from studen_doc.ir import (
    Inlines,
    ResolvedReport,
    RFigure,
    RFormula,
    RHeading,
    RList,
    RNode,
    RParagraph,
    RTable,
)
from studen_doc.model.inline import Code, LineBreak, Math, Text
from studen_doc.model.inline import Ref as RefNode
from studen_doc.render import Renderer
from studen_doc.universities.suai import SUAI


class MarkdownRenderer:
    """Читает IR: номера и ссылки уже посчитаны, рендереру остаётся только «нарисовать»."""

    def render(self, report: ResolvedReport, path: Path) -> Path:
        blocks = (self._node(node, report) for node in report.nodes)
        path.write_text("\n\n".join(filter(None, blocks)), encoding="utf-8")
        return path

    def _inline(self, inlines: Inlines, report: ResolvedReport) -> str:
        parts: list[str] = []
        for node in inlines:
            match node:
                case Text(text=text, bold=bold):
                    parts.append(f"**{text}**" if bold else text)
                case Code(text=text):
                    parts.append(f"`{text}`")
                case Math(latex=latex):
                    parts.append(f"${latex}$")
                case RefNode(label=label):
                    parts.append(report.labels[label].display)
                case LineBreak():
                    parts.append("  \n")
        return "".join(parts)

    def _node(self, node: RNode, report: ResolvedReport) -> str:
        match node:
            case RHeading(level=level, title=title, number=number):
                return f"{'#' * level} {number + ' ' if number else ''}{title}"
            case RParagraph(inlines=inlines):
                return self._inline(inlines, report)
            case RFigure(caption=caption, number=number):
                return f"![Рисунок {number.display} — {self._inline(caption, report)}]()"
            case RTable(caption=caption, number=number, header=header, rows=rows):
                title = ""
                if caption and number:
                    title = f"Таблица {number.display} — {self._inline(caption, report)}\n\n"
                head = self._row([self._inline(cell, report) for cell in header])
                rule = self._row(["---"] * len(header))
                body = [self._row([self._inline(cell.inlines, report) for cell in row]) for row in rows]
                return title + "\n".join([head, rule, *body])
            case RFormula(latex=latex, number=number):
                return f"$$ {latex} $$" + (f" ({number.display})" if number else "")
            case RList(items=items):
                return "\n".join(f"- {self._inline(item.inlines, report)}" for item in items)
            case _:
                return ""

    @staticmethod
    def _row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"


def test_markdown_renderer_consumes_the_same_ir(tmp_path):
    report = Report(SUAI)
    report.add_section(
        "Ход работы",
        P("См. рисунок ", Ref("fig:a"), " и формулу $x^2$."),
        Subsection("Подраздел", Figure(png(), "Подпись", label="fig:a"),
                   Table(["A", "B"], [["1", "x"], ["2", "y"]], caption="Итоги", label="tab:t"),
                   Formula("E=mc^2", label="eq:e"), Bullets(["раз", "два"])),
    )
    renderer: Renderer = MarkdownRenderer()
    text = renderer.render(report.resolve(), tmp_path / "out.md").read_text(encoding="utf-8")

    assert "# 1 Ход работы" in text and "## 1.1 Подраздел" in text
    assert "См. рисунок 1 и формулу $x^2$." in text                 # ссылка стала номером
    assert "![Рисунок 1 — Подпись]()" in text
    assert "Таблица 1 — Итоги\n\n| A | B |\n| --- | --- |\n| 1 | x |\n| 2 | y |" in text
    assert "$$ E=mc^2 $$ (1)" in text and "- раз\n- два" in text
