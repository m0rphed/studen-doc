"""
Общие фикстуры: стили и титульные листы, зарегистрированные тестом, убираются из реестров после него.
"""

import contextlib

import pytest

from studen_doc.model.report import register_title_page, unregister_title_page
from studen_doc.style import register_style, unregister_style


@pytest.fixture
def temporary_style():
    names: list[str] = []

    def register(name, style):
        registered = register_style(name, style)
        names.append(name)
        return registered

    yield register
    for name in names:
        with contextlib.suppress(KeyError):  # тест мог убрать имя сам
            unregister_style(name)


@pytest.fixture
def temporary_title_page():
    names: list[str] = []

    def register(name):
        decorator = register_title_page(name)

        def apply(cls):
            registered = decorator(cls)
            names.append(name)
            return registered

        return apply

    yield register
    for name in names:
        with contextlib.suppress(KeyError):
            unregister_title_page(name)
