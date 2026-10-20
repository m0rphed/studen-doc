"""
Порядок дочерних элементов WordprocessingML по схеме ECMA-376.

Word и другие программы ждут детей ``w:pPr``, ``w:tblPr``, ``w:tcPr`` и других контейнеров в строго
заданном порядке. Элемент, добавленный не на свое место, в лучшем случае игнорируется, в худшем файл
считается поврежденным. python-docx следит за порядком только для известных ему элементов, поэтому остальные
(рамка и заливка абзаца, границы и заливка ячеек, поля таблицы, настройки документа) вставляются через
``insert_ordered`` по спискам ниже.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from docx.oxml.ns import nsmap, qn
from lxml import etree

from studen_doc.ooxml.elements import Attributes, element

#: ``w:pPr`` - свойства абзаца.
PPR_ORDER: Final = (
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr", "w:widowControl", "w:numPr",
    "w:suppressLineNumbers", "w:pBdr", "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd",
    "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr",
    "w:sectPr", "w:pPrChange",
)  # fmt: skip

#: ``w:tblPr`` - свойства таблицы.
TBL_PR_ORDER: Final = (
    "w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual", "w:tblStyleRowBandSize", "w:tblStyleColBandSize",
    "w:tblW", "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout", "w:tblCellMar",
    "w:tblLook", "w:tblCaption", "w:tblDescription", "w:tblPrChange",
)  # fmt: skip

#: ``w:tcPr`` - свойства ячейки.
TC_PR_ORDER: Final = (
    "w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders", "w:shd", "w:noWrap", "w:tcMar",
    "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark", "w:headers", "w:cellIns", "w:cellDel",
    "w:cellMerge", "w:tcPrChange",
)  # fmt: skip

#: ``w:style`` - описание стиля.
STYLE_ORDER: Final = (
    "w:name", "w:aliases", "w:basedOn", "w:next", "w:link", "w:autoRedefine", "w:hidden", "w:uiPriority",
    "w:semiHidden", "w:unhideWhenUsed", "w:qFormat", "w:locked", "w:personal", "w:personalCompose",
    "w:personalReply", "w:rsid", "w:pPr", "w:rPr", "w:tblPr", "w:trPr", "w:tcPr", "w:tblStylePr",
)  # fmt: skip

#: ``w:numPr`` - принадлежность абзаца списку.
NUM_PR_ORDER: Final = ("w:ilvl", "w:numId", "w:numberingChange", "w:ins")

#: Стороны границы (``w:tcBorders``, ``w:tblBorders``): сверху, слева, снизу, справа, внутренние.
BORDER_SIDES_ORDER: Final = (
    "w:top", "w:left", "w:start", "w:bottom", "w:right", "w:end", "w:insideH", "w:insideV", "w:tl2br", "w:tr2bl",
)  # fmt: skip

#: ``w:settings`` - настройки документа (полный порядок из схемы: нужен, чтобы вставлять в середину).
SETTINGS_ORDER: Final = (
    "w:writeProtection", "w:view", "w:zoom", "w:removePersonalInformation", "w:removeDateAndTime",
    "w:doNotDisplayPageBoundaries", "w:displayBackgroundShape", "w:printPostScriptOverText",
    "w:printFractionalCharacterWidth", "w:printFormsData", "w:embedTrueTypeFonts", "w:embedSystemFonts",
    "w:saveSubsetFonts", "w:saveFormsData", "w:mirrorMargins", "w:alignBordersAndEdges",
    "w:bordersDoNotSurroundHeader", "w:bordersDoNotSurroundFooter", "w:gutterAtTop", "w:hideSpellingErrors",
    "w:hideGrammaticalErrors", "w:activeWritingStyle", "w:proofState", "w:formsDesign", "w:attachedTemplate",
    "w:linkStyles", "w:stylePaneFormatFilter", "w:stylePaneSortMethod", "w:documentType", "w:mailMerge",
    "w:revisionView", "w:trackRevisions", "w:doNotTrackMoves", "w:doNotTrackFormatting", "w:documentProtection",
    "w:autoFormatOverride", "w:styleLockTheme", "w:styleLockQFSet", "w:defaultTabStop", "w:autoHyphenation",
    "w:consecutiveHyphenLimit", "w:hyphenationZone", "w:doNotHyphenateCaps", "w:showEnvelope", "w:summaryLength",
    "w:clickAndTypeStyle", "w:defaultTableStyle", "w:evenAndOddHeaders", "w:bookFoldRevPrinting",
    "w:bookFoldPrinting", "w:bookFoldPrintingSheets", "w:drawingGridHorizontalSpacing",
    "w:drawingGridVerticalSpacing", "w:displayHorizontalDrawingGridEvery", "w:displayVerticalDrawingGridEvery",
    "w:doNotUseMarginsForDrawingGridOrigin", "w:drawingGridHorizontalOrigin", "w:drawingGridVerticalOrigin",
    "w:doNotShadeFormData", "w:noPunctuationKerning", "w:characterSpacingControl", "w:printTwoOnOne",
    "w:strictFirstAndLastChars", "w:noLineBreaksAfter", "w:noLineBreaksBefore", "w:savePreviewPicture",
    "w:doNotValidateAgainstSchema", "w:saveInvalidXml", "w:ignoreMixedContent", "w:alwaysShowPlaceholderText",
    "w:doNotDemarcateInvalidXml", "w:saveXmlDataOnly", "w:useXSLTWhenSaving", "w:saveThroughXslt",
    "w:showXMLTags", "w:alwaysMergeEmptyNamespace", "w:updateFields", "w:hdrShapeDefaults", "w:footnotePr",
    "w:endnotePr", "w:compat", "w:docVars", "w:rsids", "m:mathPr", "w:attachedSchema", "w:themeFontLang",
    "w:clrSchemeMapping", "w:doNotIncludeSubdocsInStats", "w:doNotAutoCompressPictures", "w:forceUpgrade",
    "w:captions", "w:readModeInkLockDown", "w:smartTagType", "sl:schemaLibrary", "w:shapeDefaults",
    "w:doNotEmbedSmartTags", "w:decimalSymbol", "w:listSeparator",
)  # fmt: skip

_PREFIX_BY_NAMESPACE: Final = {uri: prefix for prefix, uri in nsmap.items()}


def _prefixed_tag(node: etree._Element) -> str:
    """
    Имя элемента с префиксом (``w:shd``) по его имени в нотации Кларка (``{uri}shd``).
    """
    uri, _, local = node.tag[1:].partition("}")
    return f"{_PREFIX_BY_NAMESPACE[uri]}:{local}"


def insert_ordered(parent: etree._Element, child: etree._Element, order: Sequence[str]) -> None:
    """
    Вставляет ``child`` в ``parent`` так, чтобы порядок детей соответствовал схеме ``order``:
    перед первым из уже существующих элементов, которые по схеме идут после него, либо в конец.
    """
    tag = _prefixed_tag(child)
    if tag not in order:
        raise ValueError(f"Элемента {tag} нет в списке порядка: {', '.join(order[:3])}...")
    successors = {qn(name) for name in order[order.index(tag) + 1 :]}
    for existing in parent:
        if existing.tag in successors:
            existing.addprevious(child)
            return
    parent.append(child)


def ensure_child(
    parent: etree._Element,
    tag: str,
    order: Sequence[str],
    attrs: Attributes | None = None,
) -> etree._Element:
    """
    Дочерний элемент ``tag``: существующий (атрибуты ``attrs`` на нем не меняются) либо новый на своем месте.
    """
    existing = parent.find(qn(tag))
    if existing is not None:
        return existing
    child = element(tag, attrs)
    insert_ordered(parent, child, order)
    return child
