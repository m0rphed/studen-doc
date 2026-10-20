"""
Метки и ссылки: строковые метки блоков (``label="fig:x"``) и ссылки на сами блоки (``block.ref``).
"""

from __future__ import annotations

from studen_doc.errors import ResolveError
from studen_doc.ir import Number
from studen_doc.model.blocks import Figure, Formula, Listing, Table
from studen_doc.model.inline import BlockRef, Ref

#: Блоки, у которых бывает номер и метка.
type Labeled = Figure | Table | Listing | Formula

#: Начало внутреннего имени метки блока: автор такие имена не пишет (в начале стоит нулевой символ).
_BLOCK_LABEL_PREFIX = "\0block:"


def _block_label(block: object) -> str:
    return f"{_BLOCK_LABEL_PREFIX}{id(block)}"


class LabelRegistry:
    """
    Реестр одного прохода: какие блоки получили какие номера, на что ссылается текст и всё ли найдено.

    Блоки различаются по тождеству объекта (``id``), поэтому ``block.ref`` работает и без строковой метки.
    """

    def __init__(self) -> None:
        self._labels: dict[str, Number] = {}
        self._numbers: dict[int, Number] = {}
        self._duplicates: set[int] = set()  # один и тот же объект блока встретился в отчете несколько раз
        self._used: set[str] = set()  # строковые метки, на которые есть ссылки
        self._referenced: dict[int, object] = {}  # блоки, на которые есть ``block.ref``

    def register(self, block: Labeled, number: Number) -> None:
        """
        Запоминает номер блока под его меткой (если она есть) и по тождеству.
        """
        if block.label:
            if block.label in self._labels:
                raise ResolveError(f"Метка {block.label!r} уже используется")
            self._labels[block.label] = number
        if id(block) in self._numbers:
            self._duplicates.add(id(block))
        else:
            self._numbers[id(block)] = number

    def use(self, ref: Ref) -> None:
        """
        Текст ссылается на строковую метку.
        """
        self._used.add(ref.label)

    def reference_block(self, ref: BlockRef) -> Ref:
        """
        Текст ссылается на блок: ссылка получает внутреннюю метку, по которой рендерер найдет номер.
        """
        self._referenced[id(ref.target)] = ref.target
        return Ref(_block_label(ref.target), ref.bold, ref.italic)

    def labels(self) -> dict[str, Number]:
        """
        Все метки для рендерера: заданные автором и внутренние метки блоков, на которые есть ``block.ref``.
        """
        internal = {
            _block_label(block): self._numbers[block_id]
            for block_id, block in self._referenced.items()
            if block_id in self._numbers
        }
        return {**self._labels, **internal}

    def check(self) -> None:
        """
        Все ссылки должны находить блок с номером, и однозначно.
        """
        unknown = self._used - self._labels.keys()
        if unknown:
            raise ResolveError(f"Ссылки на неизвестные метки: {sorted(unknown)}; известные: {sorted(self._labels)}")
        for block_id, block in self._referenced.items():
            if block_id not in self._numbers:
                raise ResolveError(
                    f"block.ref указывает на {type(block).__name__}, которого нет в отчете или у которого нет номера "
                    "(таблица и листинг нумеруются при наличии подписи, формула - при метке или numbered=True)"
                )
            if block_id in self._duplicates:
                raise ResolveError(
                    f"block.ref неоднозначен: один объект {type(block).__name__} вставлен в отчет несколько раз"
                )
