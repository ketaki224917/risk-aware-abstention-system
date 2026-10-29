"""Small standard-library OOXML writer for downloadable prediction reports."""

from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

_SECTION_TITLES = {
    "RESULT": "Result",
    "REPORT SUMMARY": "Report summary",
    "WHY THE MODEL LEANED THIS WAY": "Why the model leaned this way",
    "INPUTS": "Answers provided",
    "HELD-OUT DATASET CHECK": "Held-out dataset check",
    "LIMITS": "Limits",
}
_TABLE_SECTIONS = {"RESULT", "INPUTS", "HELD-OUT DATASET CHECK"}


def _run(text: str, *, bold: bool = False, color: str | None = None) -> str:
    properties = []
    if bold:
        properties.append("<w:b/>")
    if color:
        properties.append(f'<w:color w:val="{escape(color)}"/>')
    run_properties = f"<w:rPr>{''.join(properties)}</w:rPr>" if properties else ""
    return f'<w:r>{run_properties}<w:t xml:space="preserve">{escape(str(text))}</w:t></w:r>'


def _paragraph(
    text: str,
    *,
    style: str = "Normal",
    bold: bool = False,
    color: str | None = None,
) -> str:
    return (
        f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{_run(text, bold=bold, color=color)}</w:p>'
    )


def _table(rows: list[tuple[str, str]], *, value_header: str) -> str:
    widths = (2600, 7340)
    edges = "".join(
        f'<w:{edge} w:val="single" w:sz="4" w:space="0" w:color="D9D9D9"/>'
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    xml = [
        '<w:tbl><w:tblPr><w:tblW w:w="9940" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/><w:tblBorders>' + edges + "</w:tblBorders><w:tblCellMar>"
        '<w:top w:w="90" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="90" w:type="dxa"/><w:right w:w="120" w:type="dxa"/>'
        "</w:tblCellMar></w:tblPr>"
        '<w:tblGrid><w:gridCol w:w="2600"/><w:gridCol w:w="7340"/></w:tblGrid>'
    ]
    for row_index, row in enumerate([("Field", value_header), *rows]):
        header_flag = "<w:tblHeader/>" if row_index == 0 else ""
        xml.append(f"<w:tr><w:trPr>{header_flag}<w:cantSplit/></w:trPr>")
        for column, value in enumerate(row):
            if row_index == 0:
                fill, color, bold = "24476B", "FFFFFF", True
            else:
                fill = "F1F6FA" if row_index % 2 else "FFFFFF"
                color, bold = "000000", column == 0
            xml.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{widths[column]}" w:type="dxa"/>'
                f'<w:shd w:fill="{fill}"/><w:vAlign w:val="center"/></w:tcPr>'
                f"{_paragraph(value, style='TableText', bold=bold, color=color)}</w:tc>"
            )
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def _styles() -> str:
    return """<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/>
      <w:sz w:val="21"/><w:color w:val="17212B"/></w:rPr></w:rPrDefault>
      <w:pPrDefault><w:pPr><w:spacing w:after="110" w:line="270" w:lineRule="auto"/>
      </w:pPr></w:pPrDefault></w:docDefaults>
      <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>
      </w:style>
      <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/>
        <w:basedOn w:val="Normal"/><w:next w:val="Subtitle"/>
        <w:pPr><w:spacing w:before="0" w:after="100"/><w:keepNext/></w:pPr>
        <w:rPr><w:rFonts w:ascii="Aptos Display" w:hAnsi="Aptos Display"/><w:b/>
        <w:sz w:val="36"/><w:color w:val="000000"/></w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/>
        <w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="70"/></w:pPr>
        <w:rPr><w:sz w:val="23"/><w:color w:val="000000"/></w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>
        <w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
        <w:pPr><w:keepNext/><w:spacing w:before="190" w:after="90"/></w:pPr>
        <w:rPr><w:b/><w:sz w:val="25"/><w:color w:val="000000"/></w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/>
        <w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="245"/></w:pPr>
        <w:rPr><w:sz w:val="19"/></w:rPr>
      </w:style>
    </w:styles>"""


def build_prediction_report_docx(report_text: str) -> bytes:
    """Format the generated prediction report as a Word document in memory."""
    lines = report_text.splitlines()
    if len(lines) < 2:
        raise ValueError("Prediction report is missing its title or generated time.")

    body = [
        _paragraph("Risk Aware Abstention System", style="Title"),
        _paragraph("Prediction report", style="Subtitle"),
        _paragraph(lines[1], style="Subtitle"),
    ]
    section: str | None = None
    rows: list[tuple[str, str]] = []
    paragraphs: list[str] = []

    def flush_section() -> None:
        nonlocal rows, paragraphs
        if section in _TABLE_SECTIONS and rows:
            value_header = "Answer" if section == "INPUTS" else "Value"
            body.append(_table(rows, value_header=value_header))
        body.extend(_paragraph(item) for item in paragraphs)
        rows, paragraphs = [], []

    for line in lines[2:]:
        if not line.strip():
            continue
        if line in _SECTION_TITLES:
            flush_section()
            section = line
            body.append(_paragraph(_SECTION_TITLES[line], style="Heading1"))
            continue
        if section in _TABLE_SECTIONS:
            item = line[2:] if line.startswith("- ") else line
            if ": " in item:
                label, value = item.split(": ", maxsplit=1)
                rows.append((label.rstrip(":"), value))
            elif item.endswith(":"):
                rows.append((item[:-1], ""))
            else:
                paragraphs.append(item)
        elif section == "WHY THE MODEL LEANED THIS WAY" and line.startswith("- "):
            paragraphs.append("• " + line[2:])
        else:
            paragraphs.append(line)
    flush_section()

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(body) + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1120" w:right="1150" w:bottom="1120" w:left="1150" '
        'w:header="600" w:footer="600" w:gutter="0"/></w:sectPr>'
        "</w:body></w:document>"
    )
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        "<cp:coreProperties "
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:title>Risk Aware Abstention System Prediction Report</dc:title>"
        "<dc:creator>Risk Aware Abstention System</dc:creator>"
        "<cp:lastModifiedBy>Risk Aware Abstention System</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{escape(timestamp)}</dcterms:created>'
        "</cp:coreProperties>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )
    package_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/'
        'metadata/core-properties" '
        'Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'extended-properties" '
        'Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        "</Relationships>"
    )
    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        "<Properties "
        'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        "<Application>Microsoft Word</Application>"
        "<Company>Risk Aware Abstention System</Company>"
        "</Properties>"
    )
    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
        for name, content in (
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", package_rels),
            ("word/document.xml", document_xml),
            ("word/styles.xml", _styles()),
            ("word/_rels/document.xml.rels", document_rels),
            ("docProps/core.xml", core_xml),
            ("docProps/app.xml", app_xml),
        ):
            archive.writestr(name, content.encode("utf-8"))
    return output.getvalue()
