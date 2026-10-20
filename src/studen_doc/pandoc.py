"""
Запуск pandoc: поиск исполняемого файла и кроссплатформенный вызов процесса.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from studen_doc.errors import PandocError

__all__ = ["PandocError", "PandocResult", "find_pandoc", "run_pandoc"]

#: На Windows не показывать консольное окно при запуске из GUI-приложений; на других системах значение 0 допустимо.
_CREATION_FLAGS: int = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


@dataclass(frozen=True, slots=True)
class PandocResult:
    stdout: bytes
    diagnostics: str  # stderr: предупреждения pandoc (при успешном завершении тоже бывают)


def find_pandoc() -> str | None:
    """
    Исполняемый файл pandoc: переменная ``PANDOC`` -> бинарник из pypandoc-binary -> ``PATH``.
    Порядок даёт воспроизводимость: по умолчанию у всех одна и та же (встроенная) версия pandoc.
    """
    if explicit := os.environ.get("PANDOC"):
        return explicit
    try:
        import pypandoc

        return pypandoc.get_pandoc_path()
    except (ImportError, OSError):
        return shutil.which("pandoc")  # учитывает PATHEXT на Windows


def run_pandoc(
    args: Sequence[str],
    data: bytes,
    *,
    command: Sequence[str] | None = None,
    timeout_s: float = 120.0,
) -> PandocResult:
    """
    Запускает pandoc списком аргументов без оболочки; обмен - байтами UTF-8, поэтому поведение
    одинаково на Windows и Linux.

    ``command`` - команда запуска без аргументов (``["pandoc"]``, в тестах - ``[sys.executable, "fake_pandoc.py"]``);
    ``None`` - найти автоматически.
    """
    if command is None:
        found = find_pandoc()
        if found is None:
            raise PandocError(
                "pandoc не найден: установите пакет pypandoc-binary, добавьте pandoc в PATH "
                "или задайте переменную окружения PANDOC"
            )
        command = [found]
    try:
        process = subprocess.run(
            [*command, *args],
            input=data,
            capture_output=True,
            timeout=timeout_s,
            check=False,
            creationflags=_CREATION_FLAGS,
        )
    except FileNotFoundError as error:
        raise PandocError(f"Не удалось запустить pandoc: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise PandocError(f"pandoc не ответил за {timeout_s:g} с") from error

    diagnostics = process.stderr.decode("utf-8", "replace").strip()
    if process.returncode != 0:
        raise PandocError(f"pandoc завершился с кодом {process.returncode}: {diagnostics[:500]}")
    return PandocResult(process.stdout, diagnostics)
