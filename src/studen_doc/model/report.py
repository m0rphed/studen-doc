"""
Модель отчёта: разделы, оглавление, титульный лист и сам ``Report``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from studen_doc.model.blocks import Block
from studen_doc.numfmt import MINUS

if TYPE_CHECKING:
    from studen_doc.equations import MathConverter
    from studen_doc.ir import ResolvedReport
    from studen_doc.model.bibliography import Bibliography, SourceFormatter
    from studen_doc.model.inline import InlineParser
    from studen_doc.style import ReportStyle
    from studen_doc.style.headings import AppendixStatus, SectionName


class TitlePage:
    """
    Базовый класс титульных листов.

    Титульный лист — только данные. Как его нарисовать в конкретном формате, определяет рендерер этого
    формата (см. ``studen_doc.render.docx.title.render_title``). Чтобы титульный лист можно было
    задать в метаданных Markdown (``title_page: {type: имя}``), класс регистрируют декоратором
    ``register_title_page``.
    """


_TITLE_PAGES: dict[str, type[TitlePage]] = {}


def register_title_page[T: type[TitlePage]](name: str) -> Callable[[T], T]:
    """
    Декоратор класса: регистрирует титульный лист под именем. Ставится над ``@dataclass``:

        @register_title_page("suai")
        @dataclass(kw_only=True)
        class TitlePageSUAI(TitlePage): ...
    """

    def register(cls: T) -> T:
        if name in _TITLE_PAGES:
            raise ValueError(f"Титульный лист {name!r} уже зарегистрирован")
        _TITLE_PAGES[name] = cls
        return cls

    return register


def unregister_title_page(name: str) -> None:
    """
    Убирает титульный лист из реестра; неизвестное имя - ``KeyError``. Вёрстка, добавленная через
    ``render_title.register``, остается за классом: она никому не мешает, пока класс недоступен по имени.
    """
    del _TITLE_PAGES[name]


def title_page_named(name: str) -> type[TitlePage]:
    """
    Класс титульного листа по имени; неизвестное имя - ``KeyError`` (допустимые - ``title_page_names()``).
    """
    return _TITLE_PAGES[name]


def title_page_names() -> list[str]:
    return sorted(_TITLE_PAGES)


@dataclass(frozen=True, slots=True)
class Section:
    """
    Раздел верхнего уровня: ``title`` - что печатается в заголовке, ``rule`` - по какому правилу он оформляется
    (ключ ``HeadingsStyle.rules``: «Введение», «Основная часть», «Приложение»...). Без ``rule`` правило ищется
    по самому заголовку.
    """

    title: SectionName
    content: tuple[Block, ...]
    rule: SectionName | None = None
    status: AppendixStatus | None = None  # для приложений: «обязательное», «справочное»

    @property
    def rule_name(self) -> str:
        """
        Ключ правил оформления: заданное ``rule`` либо сам заголовок.
        """
        return self.rule if self.rule is not None else self.title


@dataclass(frozen=True, slots=True)
class Toc:
    title: str | None = None  # None -> ReportStyle.toc_title
    _: KW_ONLY
    levels: int = 3
    page_break_after: bool = True  # по ГОСТ содержание — на отдельной странице


@dataclass
class Report:
    """
    Отчёт = стиль + содержимое. Сборка — отдельный шаг: ``resolve`` -> рендерер выбранного формата.
    """

    style: ReportStyle
    title: str | None = None        # свойство документа «Название»
    author: str | None = None
    title_page: TitlePage | None = None
    bibliography: Bibliography | None = None  # откуда брать описания источников для ``Sources``
    items: list[Section | Toc] = field(default_factory=list)

    @classmethod
    def from_markdown(
        cls,
        *sources: str | Path,
        style: ReportStyle | None = None,
        title_page: TitlePage | None = None,
        title: str | None = None,
        author: str | None = None,
        bibliography: Bibliography | None = None,
        inserts: Mapping[str, Block | Sequence[Block]] | None = None,
        variables: Mapping[str, Any] | None = None,
        decimal: str = ",",
        minus: str = MINUS,
        command: Sequence[str] | None = None,
    ) -> Self:
        """
        Отчет из одного или нескольких файлов Markdown (содержимое файлов идет подряд).

        ``style``, ``title_page``, ``title``, ``author`` и ``bibliography`` по умолчанию берутся из блока метаданных
        YAML первого файла, где они заданы (``style: suai``, ``title_page: {type: suai, ...}``,
        ``bibliography: refs.bib``); явные аргументы важнее метаданных.

        Python и Markdown смешиваются так: ``inserts={"таблица": Table(...)}`` подставляются вместо
        ``::: {.insert name=таблица}``, ``variables={"r2": 0.881}`` - вместо ``[]{var=r2 format=".3f"}``
        (``decimal`` - десятичный разделитель, ``minus`` - знак минус в числах; по умолчанию запятая и U+2212).
        ``command`` - свой запуск pandoc (по умолчанию ищется автоматически).
        """
        from studen_doc.frontends.markdown import load_report  # лениво: фронтенд зависит от модели

        return load_report(
            *sources,
            report_class=cls,
            style=style,
            title_page=title_page,
            title=title,
            author=author,
            bibliography=bibliography,
            inserts=inserts,
            variables=variables,
            decimal=decimal,
            minus=minus,
            command=command,
        )

    def add_title_page(self, title_page: TitlePage) -> Self:
        self.title_page = title_page
        return self

    def add_toc(self, title: str | None = None, *, levels: int = 3, page_break_after: bool = True) -> Self:
        self.items.append(Toc(title, levels=levels, page_break_after=page_break_after))
        return self

    def add_section(
        self,
        title: SectionName,
        *content: Block,
        rule: SectionName | None = None,
        status: AppendixStatus | None = None,
    ) -> Self:
        """
        Раздел верхнего уровня. ``title`` - заголовок; по нему же выбирается правило оформления, если
        не задано ``rule``:

            add_section("Введение", ...)
            add_section("Описание данных", ..., rule="Основная часть")  # свой заголовок, оформление основной части
            add_section("Исходный код", ..., rule="Приложение", status="справочное")

        ``status`` - статус приложения, печатается под его номером: «обязательное», «справочное».
        """
        self.items.append(Section(title, content, rule, status))
        return self

    def resolve(
        self,
        *,
        inline_parser: InlineParser | None = None,
        source_formatter: SourceFormatter | None = None,
    ) -> ResolvedReport:
        """
        Проход нумерации и ссылок: модель -> промежуточное представление (не зависит от формата).

        ``inline_parser`` - свой разбор строк ``Md`` (по умолчанию pandoc, один вызов на документ),
        ``source_formatter`` - свое оформление записей библиографии (по умолчанию pandoc citeproc).
        """
        from studen_doc.pipeline import resolve  # лениво: конвейер зависит от модели

        return resolve(self, inline_parser=inline_parser, source_formatter=source_formatter)

    def build_to_docx(
        self,
        path: str | Path,
        *,
        math: MathConverter | None = None,
        inline_parser: InlineParser | None = None,
        source_formatter: SourceFormatter | None = None,
    ) -> Path:
        """
        Собирает .docx. ``math`` - свой конвертер формул, ``inline_parser`` - свой разбор ``Md``,
        ``source_formatter`` - свое оформление записей библиографии (по умолчанию все делает pandoc).
        """
        from studen_doc.pipeline import build_docx  # лениво: конвейер зависит от модели

        return build_docx(self, path, math=math, inline_parser=inline_parser, source_formatter=source_formatter)
