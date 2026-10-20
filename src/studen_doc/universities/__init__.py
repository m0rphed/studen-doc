"""
Оформление конкретных вузов: пресеты стиля и титульные листы.

Импорт пакета регистрирует их под именами (``register_style``, ``register_title_page``), поэтому в метаданных
Markdown достаточно написать ``style: suai`` и ``title_page: {type: suai, ...}``. Подключается пакет явно:
``import studen_doc.universities`` (он загружает python-docx для вёрстки титульного листа). Свой вуз
добавляется тем же способом в любом модуле, который импортируется до сборки отчета.
"""

from studen_doc.universities.suai import SUAI, TitlePageSUAI

__all__ = ["SUAI", "TitlePageSUAI"]
