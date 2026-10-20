"""
Рисунки из matplotlib.
"""

from __future__ import annotations

import io
from typing import Any

from studen_doc.model.blocks import Figure
from studen_doc.model.inline import RichText


def figure_from_matplotlib(
    figure: Any,
    caption: RichText,
    *,
    label: str | None = None,
    width_cm: float | None = None,
    dpi: int = 200,
) -> Figure:
    """
    Блок ``Figure`` из рисунка matplotlib (``Figure`` или ``Axes``): растр PNG в памяти, файлов на диске нет.

    Рисунок не закрывается - это забота вызывающего (``plt.close(fig)``).
    """
    target = getattr(figure, "figure", figure)  # Axes -> его Figure
    buffer = io.BytesIO()
    target.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    return Figure(buffer, caption, label=label, width_cm=width_cm)
