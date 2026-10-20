"""
Стиль CSL ``gost-7-32-numeric.csl`` против примеров самого ГОСТ 7.32-2017 (приложения Д и Е).

Каждый пример стандарта записан как данные (CSL JSON) вместе с текстом из стандарта. Тест оформляет данные
стилем через pandoc и сверяет результат с текстом стандарта. Стандарт в примерах непоследователен
(инициалы то ``А. Б.``, то ``А.Б.``; ``дата обращения`` то с двоеточием, то без; тире то длинное, то короткое;
в примере 1 приложения Д нет точки перед тире), поэтому сравнение идет после ``normalize``: различия в этих мелочах
не считаются. Явные опечатки стандарта (``http/www``, лигатура ``ﬁ``, перенос слова ``инфор-мационных``,
латинская ``Р.``) исправлены в ожидаемом тексте.

Кроме примеров стандарта, ``RULES`` проверяет правила ГОСТ 7.1-2003 (на него ссылается 5.10.1): издание, серия,
переводчик, том, диапазон лет, знак вопроса в конце названия, запись из одного названия.

Три списка:

* ``MATCHING`` - примеры, которые стиль воспроизводит;
* ``VARIANTS`` - примеры, где стиль сознательно оформляет иначе (текст стандарта и наш результат рядом);
* ``NOT_REPRODUCED`` - примеры, которых CSL выразить не может; ``xfail(strict=True)`` сообщит, если стиль их научится.
"""

import json
import re

import pytest

from studen_doc.bibliography import STYLE_GOST_732, PandocCiteproc
from studen_doc.model.bibliography import Bibliography
from studen_doc.model.inline import Text
from studen_doc.pandoc import find_pandoc

pytestmark = pytest.mark.skipif(find_pandoc() is None, reason="pandoc не найден")


def person(family: str, given: str) -> dict:
    return {"family": family, "given": given}


def issued(*years: int) -> dict:
    return {"date-parts": [[year] for year in years]}


def accessed(day: int, month: int, year: int) -> dict:
    return {"date-parts": [[year, month, day]]}


def normalize(text: str) -> str:
    """
    Сравнение без различий, в которых сам стандарт непоследователен.
    """
    text = text.replace(" ", " ").replace("–", "—")
    text = re.sub(r"(?<=\.)\s+(?=[A-ZА-ЯЁ]\.)", "", text)  # инициалы: "А. Б." == "А.Б."
    text = re.sub(r"дата обращения:", "дата обращения", text)
    return re.sub(r"\s+", " ", text).strip()


def render(tmp_path, items: list[dict]) -> dict[str, str]:
    refs = tmp_path / "refs.json"
    refs.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    entries = PandocCiteproc(Bibliography(refs, csl=STYLE_GOST_732))([item["id"] for item in items])
    return {key: "".join(node.text for node in inlines if isinstance(node, Text)) for key, inlines in entries.items()}


# --------------------------------------------------------------------------------------------- примеры
MATCHING = {
    "Д.4 статья, два автора": (
        {
            "type": "article-journal",
            "author": [person("Антопольский", "А. Б."), person("Белоозеров", "В. Н.")],
            "title": "Процедура формирования макротезауруса политематических информационных систем",
            "container-title": "Классификация и кодирование",
            "issued": issued(1976),
            "issue": "1 (57)",
            "page": "25-29",
        },
        "Антопольский А. Б., Белоозеров В. Н. Процедура формирования макротезауруса политематических "
        "информационных систем // Классификация и кодирование. — 1976. — № 1 (57). — С. 25—29.",
    ),
    "Д.10 статья, серия в названии журнала": (
        {
            "type": "article-journal",
            "author": [person("Смирнова", "О. В.")],
            "title": "Методика составления индексов УДК",
            "container-title": "Научно-техническая информация. Сер. 1",
            "issued": issued(2008),
            "issue": "8",
            "page": "7-8",
        },
        "Смирнова О.В. Методика составления индексов УДК // Научно-техническая информация. Сер. 1. — 2008. — "
        "№ 8. — С. 7—8.",
    ),
    "Д.8 стандарт, место и год без издательства": (
        {
            "type": "book",
            "title": "ГОСТ 7.25—2001 СИБИД. Тезаурус информационно-поисковый одноязычный. Правила разработки, "
            "структура, состав и форма представления",
            "publisher-place": "М.",
            "issued": issued(2002),
            "number-of-pages": "16",
        },
        "ГОСТ 7.25—2001 СИБИД. Тезаурус информационно-поисковый одноязычный. Правила разработки, структура, "
        "состав и форма представления. — М., 2002. — 16 с.",
    ),
    "Д.14 электронный ресурс без даты обращения": (
        {"type": "webpage", "title": "Рубрикатор по нанонауке и нанотехнологиям", "URL": "http://www.rubric.neicon.ru"},
        "Рубрикатор по нанонауке и нанотехнологиям. — URL: http://www.rubric.neicon.ru.",
    ),
    "Е статья": (
        {
            "type": "article-journal",
            "author": [person("Гуреев", "В. Н."), person("Мазов", "Н. А.")],
            "title": "Использование библиометрии для оценки значимости журналов в научных библиотеках (обзор)",
            "container-title": "Научно-техническая информация. Сер. 1",
            "issued": issued(2015),
            "issue": "2",
            "page": "8-19",
        },
        "Гуреев В.Н., Мазов Н.А. Использование библиометрии для оценки значимости журналов в научных "
        "библиотеках (обзор) // Научно-техническая информация. Сер. 1. — 2015. — № 2. — С. 8—19.",
    ),
    "Е статья, заглавие с двоеточием": (
        {
            "type": "article-journal",
            "author": [person("Колкова", "Н. И."), person("Скипор", "И. Л.")],
            "title": "Терминосистема предметной области «электронные информационные ресурсы»: взгляд с позиций "
            "теории и практики",
            "container-title": "Научн. и техн. б-ки",
            "issued": issued(2016),
            "issue": "7",
            "page": "24-41",
        },
        "Колкова Н.И., Скипор И.Л. Терминосистема предметной области «электронные информационные ресурсы»: "
        "взгляд с позиций теории и практики // Научн. и техн. б-ки. — 2016. — № 7. — С. 24—41.",
    ),
    "Е книга, два автора": (
        {
            "type": "book",
            "author": [person("Земсков", "А. И."), person("Шрайберг", "Я. Л.")],
            "title": "Электронные библиотеки: учебник для вузов",
            "publisher-place": "М.",
            "publisher": "Либерея",
            "issued": issued(2003),
            "number-of-pages": "351",
        },
        "Земсков А.И., Шрайберг Я.Л. Электронные библиотеки: учебник для вузов. — М.: Либерея, 2003. — 351 с.",
    ),
    "Е книга, один автор": (
        {
            "type": "book",
            "author": [person("Костюк", "К. Н.")],
            "title": "Книга в новой медицинской среде",
            "publisher-place": "М.",
            "publisher": "Директ-Медиа",
            "issued": issued(2015),
            "number-of-pages": "430",
        },
        "Костюк К.Н. Книга в новой медицинской среде. — М.: Директ-Медиа, 2015. — 430 с.",
    ),
    "Е статья о конференции, три автора": (
        {
            "type": "article-journal",
            "author": [
                person("Парфенова", "С. Л."),
                person("Гришакина", "Е. Г."),
                person("Золотарев", "Д. В."),
            ],
            "title": "4-я Международная научно-практическая конференция «Научное издание международного уровня — "
            "2015: современные тенденции в мировой практике редактирования, издания и оценки научных публикаций»",
            "container-title": "Наука. Инновации. Образование",
            "issued": issued(2015),
            "issue": "17",
            "page": "241-252",
        },
        "Парфенова С.Л., Гришакина Е.Г., Золотарев Д.В. 4-я Международная научно-практическая конференция "
        "«Научное издание международного уровня — 2015: современные тенденции в мировой практике редактирования, "
        "издания и оценки научных публикаций» // Наука. Инновации. Образование. — 2015. — № 17. — С. 241—252.",
    ),
    "Е электронный ресурс с общим обозначением и годом": (
        {
            "type": "webpage",
            "title": "Статистические показатели российского книгоиздания в 2006 г.: цифры и рейтинги",
            "medium": "Электронный ресурс",
            "issued": issued(2006),
            "URL": "http://bookhamber.ru/stat_2006.htm",
            "accessed": accessed(12, 3, 2009),
        },
        "Статистические показатели российского книгоиздания в 2006 г.: цифры и рейтинги [Электронный ресурс]. — "
        "2006. — URL: http://bookhamber.ru/stat_2006.htm (дата обращения 12.03.2009).",
    ),
    "Е электронный ресурс без года": (
        {
            "type": "webpage",
            "title": "Прогноз научно-технологического развития Российской Федерации на период до 2030 года",
            "URL": "http://government.ru/media/files/41d4b737638891da2184/pdf",
            "accessed": accessed(15, 11, 2016),
        },
        "Прогноз научно-технологического развития Российской Федерации на период до 2030 года. — "
        "URL: http://government.ru/media/files/41d4b737638891da2184/pdf (дата обращения 15.11.2016).",
    ),
    "Е электронный ресурс, одно название": (
        {
            "type": "webpage",
            "title": "Web of Science",
            "URL": "http://apps.webofknowledge.com/",
            "accessed": accessed(15, 11, 2016),
        },
        "Web of Science. — URL: http://apps.webofknowledge.com/ (дата обращения 15.11.2016).",
    ),
    "Е нормативный документ с издательством": (
        {
            "type": "book",
            "title": "ГОСТ 7.0.96—2016 Система стандартов по информации, библиотечному и издательскому делу. "
            "Электронные библиотеки. Основные виды. Структура. Технология формирования",
            "publisher-place": "М.",
            "publisher": "Стандартинформ",
            "issued": issued(2016),
            "number-of-pages": "16",
        },
        "ГОСТ 7.0.96—2016 Система стандартов по информации, библиотечному и издательскому делу. Электронные "
        "библиотеки. Основные виды. Структура. Технология формирования. — М.: Стандартинформ, 2016. — 16 с.",
    ),
    "Е нормативный документ из сети": (
        {
            "type": "webpage",
            "title": "Приказ Минобразования РФ от 19 декабря 2013 г. № 1367 «Об утверждении Порядка организации и "
            "осуществления образовательной деятельности по образовательным программам высшего образования — "
            "программам бакалавриата, программам специалитета, программам магистратуры»",
            "URL": "http://www.consultant.ru/document/cons_doc_LAW_159671/",
            "accessed": accessed(4, 8, 2016),
        },
        "Приказ Минобразования РФ от 19 декабря 2013 г. № 1367 «Об утверждении Порядка организации и "
        "осуществления образовательной деятельности по образовательным программам высшего образования — "
        "программам бакалавриата, программам специалитета, программам магистратуры». — "
        "URL: http://www.consultant.ru/document/cons_doc_LAW_159671/ (дата обращения 04.08.2016).",
    ),
    "Е международный стандарт": (
        {
            "type": "webpage",
            "title": "ISO 25964-1:2011. Information and documentation — Thesauri and interoperability with other "
            "vocabularies — Part 1: Thesauri for information retrieval",
            "URL": "http://www.iso.org/iso/catalogue_detail.htm?csnumber=53657",
            "accessed": accessed(20, 10, 2016),
        },
        "ISO 25964-1:2011. Information and documentation — Thesauri and interoperability with other vocabularies — "
        "Part 1: Thesauri for information retrieval. — "
        "URL: http://www.iso.org/iso/catalogue_detail.htm?csnumber=53657 (дата обращения 20.10.2016).",
    ),
}

#: Пример стандарта и то, что выдает стиль, когда они сознательно различаются: (данные, текст стандарта, наш результат).
VARIANTS = {
    "Д.7 иностранная статья: термины всегда русские (Т., С. вместо Vol., Р.)": (
        {
            "type": "article-journal",
            "title": "Nuovo soggettario: guida al sistema italiano di indicizzazione per soggetto, prototipo del "
            "thesaurus [Рецензия]",
            "container-title": "Knowledge Organization",
            "issued": issued(2007),
            "volume": "34",
            "issue": "1",
            "page": "58-60",
        },
        "Nuovo soggettario: guida al sistema italiano di indicizzazione per soggetto, prototipo del thesaurus "
        "[Рецензия] // Knowledge Organization. — 2007. — Vol. 34, № 1. — Р. 58—60.",
        "Nuovo soggettario: guida al sistema italiano di indicizzazione per soggetto, prototipo del thesaurus "
        "[Рецензия] // Knowledge Organization. — 2007. — Т. 34, № 1. — С. 58—60.",
    ),
    "Д.11 четыре автора и редактор: авторы в заголовке, а не после косой черты": (
        {
            "type": "book",
            "author": [
                person("Антошкова", "О. А."),
                person("Астахова", "Т. С."),
                person("Белоозеров", "В. Н."),
                person("Другой", "А. А."),
            ],
            "editor": [{"literal": "акад. Ю. М. Арского"}],
            "title": "Индексирование фундаментальных научных направлений кодами информационных классификаций УДК",
            "publisher-place": "М.",
            "issued": issued(2010),
            "number-of-pages": "322",
        },
        "Индексирование фундаментальных научных направлений кодами информационных классификаций УДК / "
        "О.А. Антошкова, Т.С. Астахова, В.Н. Белоозеров и др.; под ред. акад. Ю.М. Арского. — М., 2010. — 322 с.",
        "Антошкова О. А., Астахова Т. С., Белоозеров В. Н. и др. Индексирование фундаментальных научных направлений "
        "кодами информационных классификаций УДК / под ред. акад. Ю. М. Арского. — М., 2010. — 322 с.",
    ),
}

NOT_REPRODUCED = {
    "Д.12 три автора после косой черты (в Е те же три автора идут в заголовке)": (
        {
            "type": "book",
            "author": [person("Гиляревский", "Р. С."), person("Шапкин", "А. В."), person("Белоозеров", "В. Н.")],
            "title": "Рубрикатор как инструмент информационной навигации",
            "publisher-place": "СПб.",
            "publisher": "Профессия",
            "issued": issued(2008),
            "number-of-pages": "352",
        },
        "Рубрикатор как инструмент информационной навигации / Р.С. Гиляревский, А.В. Шапкин, В.Н. Белоозеров. — "
        "СПб.: Профессия, 2008. — 352 с.",
    ),
}


#: Правила ГОСТ 7.1-2003 вне примеров 7.32: (данные, ожидаемая запись).
RULES = {
    "издание числом (как в BibLaTeX)": (
        {
            "type": "book",
            "author": [person("Иванов", "И. И.")],
            "title": "Основы",
            "edition": "3",
            "publisher-place": "М.",
            "publisher": "Наука",
            "issued": issued(2010),
            "number-of-pages": "400",
        },
        "Иванов И. И. Основы. — 3-е изд. — М.: Наука, 2010. — 400 с.",
    ),
    "издание текстом": (
        {
            "type": "book",
            "author": [person("Иванов", "И. И.")],
            "title": "Основы",
            "edition": "3-е изд., перераб. и доп.",
            "publisher-place": "М.",
            "publisher": "Наука",
            "issued": issued(2010),
            "number-of-pages": "400",
        },
        "Иванов И. И. Основы. — 3-е изд., перераб. и доп. — М.: Наука, 2010. — 400 с.",
    ),
    "серия": (
        {
            "type": "book",
            "author": [person("Иванов", "И. И.")],
            "title": "Основы",
            "publisher-place": "СПб.",
            "publisher": "Питер",
            "issued": issued(2011),
            "number-of-pages": "300",
            "collection-title": "Классика науки",
            "collection-number": "5",
        },
        "Иванов И. И. Основы. — СПб.: Питер, 2011. — 300 с. — (Классика науки ; 5).",
    ),
    "переводчик и том": (
        {
            "type": "book",
            "author": [person("Кнут", "Д.")],
            "translator": [person("Козаченко", "Ю. В.")],
            "title": "Искусство программирования",
            "publisher-place": "М.",
            "publisher": "Вильямс",
            "issued": issued(2000),
            "number-of-pages": "720",
            "volume": "1",
        },
        "Кнут Д. Искусство программирования / пер. Ю. В. Козаченко. — М.: Вильямс, 2000. — Т. 1. — 720 с.",
    ),
    "том и номер журнала": (
        {
            "type": "article-journal",
            "author": [person("Иванов", "И. И.")],
            "title": "Статья",
            "container-title": "Вестник",
            "issued": issued(2020),
            "volume": "12",
            "issue": "3",
            "page": "5-9",
        },
        "Иванов И. И. Статья // Вестник. — 2020. — Т. 12, № 3. — С. 5—9.",
    ),
    "диапазон лет": (
        {
            "type": "webpage",
            "title": "Сайт",
            "publisher": "Организация",
            "issued": issued(2006, 2013),
            "URL": "http://a.b/",
        },
        "Сайт. — Организация, 2006—2013. — URL: http://a.b/.",
    ),
    "знак вопроса в конце названия": (
        {
            "type": "book",
            "author": [person("Чернышевский", "Н. Г.")],
            "title": "Что делать?",
            "publisher-place": "М.",
            "publisher": "Наука",
            "issued": issued(1975),
            "number-of-pages": "100",
        },
        "Чернышевский Н. Г. Что делать? — М.: Наука, 1975. — 100 с.",
    ),
    "полные имена сокращаются до инициалов": (
        {
            "type": "book",
            "author": [person("Толстой", "Лев Николаевич")],
            "title": "Война и мир",
            "publisher-place": "М.",
            "publisher": "АСТ",
            "issued": issued(2005),
            "number-of-pages": "1300",
        },
        "Толстой Л. Н. Война и мир. — М.: АСТ, 2005. — 1300 с.",
    ),
    "только название": ({"type": "book", "title": "Просто название"}, "Просто название."),
}


@pytest.mark.parametrize("name", MATCHING)
def test_style_reproduces_the_example_of_the_standard(tmp_path, name):
    data, expected = MATCHING[name]
    (rendered,) = render(tmp_path, [{"id": "x", **data}]).values()
    assert normalize(rendered) == normalize(expected)


@pytest.mark.parametrize("name", RULES)
def test_style_follows_gost_7_1_rules(tmp_path, name):
    data, expected = RULES[name]
    (rendered,) = render(tmp_path, [{"id": "x", **data}]).values()
    assert rendered == expected  # без нормализации: точная запись, включая пробелы в инициалах и тире


@pytest.mark.parametrize("name", VARIANTS)
def test_deliberate_differences_from_the_standard_stay_as_documented(tmp_path, name):
    data, standard, ours = VARIANTS[name]
    (rendered,) = render(tmp_path, [{"id": "x", **data}]).values()
    assert normalize(rendered) == normalize(ours)
    assert normalize(rendered) != normalize(standard)


@pytest.mark.parametrize("name", NOT_REPRODUCED)
@pytest.mark.xfail(strict=True, reason="CSL не умеет выбирать форму записи по числу авторов")
def test_examples_csl_cannot_express(tmp_path, name):
    data, expected = NOT_REPRODUCED[name]
    (rendered,) = render(tmp_path, [{"id": "x", **data}]).values()
    assert normalize(rendered) == normalize(expected)
