"""
Оформление списка использованных источников из файлов библиографии.

Описания источников (BibTeX, BibLaTeX, CSL JSON и YAML - все, что читает pandoc) оформляет citeproc из pandoc по
стилю CSL. В пакете два стиля (лицензия CC BY-SA 3.0, см. заголовки файлов): ``gost-7-32-numeric.csl`` (по умолчанию) -
описания по примерам ГОСТ 7.32-2017 и правилам ГОСТ 7.1-2003, проверен тестами по приложениям Д и Е стандарта, и
``gost-r-7-0-5-2008-numeric.csl`` (ГОСТ Р 7.0.5-2008; автор Yurkin Maxim). Свой стиль задается
``Bibliography(files, csl="...")``.
"""

from studen_doc.bibliography.citeproc import DEFAULT_CSL, STYLE_GOST_732, STYLE_GOST_R_705, PandocCiteproc

__all__ = ["DEFAULT_CSL", "STYLE_GOST_732", "STYLE_GOST_R_705", "PandocCiteproc"]
