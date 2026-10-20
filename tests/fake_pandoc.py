"""
Подставной pandoc для тестов: markdown со стандартного ввода -> минимальный docx в стандартный вывод.

Запускается как ``[sys.executable, fake_pandoc.py, <аргументы pandoc>]`` — одинаково на Windows и Linux.
Управление через переменные окружения:
    FAKE_PANDOC_LOG   файл, в который дописывается по строке на каждый запуск (тело ввода);
    FAKE_PANDOC_MODE  fail — код возврата 3; unparsed — абзацы с «BAD» без формулы; short — на один абзац меньше.
"""

import io
import os
import sys
import zipfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def main() -> int:
    source = sys.stdin.buffer.read().decode("utf-8")
    log = os.environ.get("FAKE_PANDOC_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(source.replace("\n", "⏎") + "\n")
    mode = os.environ.get("FAKE_PANDOC_MODE", "")
    if mode == "fail":
        sys.stderr.write("boom")
        return 3
    paragraphs = []
    for chunk in source.split("\n\n"):
        text = chunk.strip().strip("$")
        if mode == "unparsed" and "BAD" in text:
            paragraphs.append(f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>")
        else:
            paragraphs.append(f"<w:p><m:oMath><m:r><m:t>{text}</m:t></m:r></m:oMath></w:p>")
    if mode == "short":
        paragraphs.pop()
    document = f'<w:document xmlns:w="{W}" xmlns:m="{M}"><w:body>{"".join(paragraphs)}</w:body></w:document>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", document)
    sys.stdout.buffer.write(buffer.getvalue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
