"""Check whether BrEaST metadata supports the app's requested questionnaire inputs.

Run with the project environment:
    python scripts/audit_breast_symptom_candidate.py
"""
from __future__ import annotations

import hashlib
import json
import posixpath
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "breast_lesions_usg_clinical.xlsx"
OUTPUT_PATH = PROJECT_ROOT / "results" / "br_east_candidate_audit" / "audit.json"
SOURCE_URL = (
    "https://www.cancerimagingarchive.net/wp-content/uploads/"
    "BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx"
)
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "relationships": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter.upper()) - ord("A") + 1
    return value - 1


def _read_first_sheet() -> list[dict[str, str]]:
    """Read the first worksheet from xlsx with standard-library OOXML support."""
    with ZipFile(DATA_PATH) as workbook:
        workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
        relationships_xml = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
        relationships = {
            item.attrib["Id"]: item.attrib["Target"] for item in relationships_xml
        }
        sheet = workbook_xml.find("main:sheets/main:sheet", NS)
        if sheet is None:
            raise ValueError("Workbook has no worksheet.")
        relation_id = sheet.attrib[f"{{{NS['relationships']}}}id"]
        target = relationships[relation_id].lstrip("/")
        if not target.startswith("xl/"):
            target = posixpath.normpath(posixpath.join("xl", target))
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            shared_xml = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            shared_strings = [
                "".join(text.text or "" for text in item.findall(".//main:t", NS))
                for item in shared_xml.findall("main:si", NS)
            ]
        worksheet_xml = ET.fromstring(workbook.read(target))
        rows: list[list[str]] = []
        for row in worksheet_xml.findall(".//main:sheetData/main:row", NS):
            cells: list[str] = []
            for cell in row.findall("main:c", NS):
                index = _column_index(cell.attrib["r"])
                while len(cells) <= index:
                    cells.append("")
                value = cell.find("main:v", NS)
                if cell.attrib.get("t") == "s" and value is not None:
                    cells[index] = shared_strings[int(value.text or "0")]
                elif cell.attrib.get("t") == "inlineStr":
                    cells[index] = "".join(
                        part.text or "" for part in cell.findall(".//main:t", NS)
                    )
                else:
                    cells[index] = value.text if value is not None else ""
            rows.append(cells)
    if not rows:
        raise ValueError("Workbook contains no rows.")
    headers = rows[0]
    return [
        dict(zip(headers, values + [""] * (len(headers) - len(values)), strict=True))
        for values in rows[1:]
    ]


def audit() -> dict[str, object]:
    rows = _read_first_sheet()
    required = {"Age", "Signs", "Symptoms", "Classification", "Verification"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Workbook is missing required columns: {sorted(required)}")

    total_classes = Counter(row["Classification"] for row in rows)
    binary_rows = [row for row in rows if row["Classification"] in {"benign", "malignant"}]
    complete_rows = [
        row
        for row in binary_rows
        if all(row[field] != "not available" for field in ("Age", "Signs", "Symptoms"))
    ]
    complete_classes = Counter(row["Classification"] for row in complete_rows)
    missing_counts = {
        field: sum(row[field] == "not available" for row in binary_rows)
        for field in ("Age", "Signs", "Symptoms")
    }
    sign_values = Counter()
    symptom_values = Counter()
    for row in rows:
        sign_values.update(row["Signs"].split("&"))
        symptom_values.update(row["Symptoms"].split("&"))

    return {
        "dataset": "BrEaST clinical metadata (candidate only; not used by the app)",
        "source": SOURCE_URL,
        "doi": "10.7937/9WKK-Q141",
        "paper_doi": "10.1038/s41597-024-02984-z",
        "license": "CC BY 4.0",
        "sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
        "rows": len(rows),
        "classification_counts": dict(total_classes),
        "biopsy_confirmed_rows": sum(
            row["Verification"] == "confirmed by biopsy" for row in rows
        ),
        "follow_up_confirmed_rows": sum(
            row["Verification"] == "confirmed by follow-up care" for row in rows
        ),
        "binary_rows": len(binary_rows),
        "binary_class_counts": dict(Counter(row["Classification"] for row in binary_rows)),
        "binary_field_missing_counts": missing_counts,
        "complete_age_signs_symptoms_rows": len(complete_rows),
        "complete_case_class_counts": dict(complete_classes),
        "recorded_sign_values": dict(sign_values),
        "recorded_symptom_values": dict(symptom_values),
        "compatibility_findings": [
            "All cases are adult women examined with breast ultrasound; this is a selected lesion cohort.",
            "The Signs field records physician-observed findings, not separate self-reported answers.",
            "The Symptoms field is an aggregated multi-select field and is missing for many cases.",
            "The data do not include height or weight and do not represent gender diversity.",
            "Four separate user symptom answers cannot be matched directly to this dataset's fields.",
        ],
        "decision": (
            "Do not use this small, incomplete, ultrasound-selected dataset to claim proper "
            "symptom-only predictions. The application continues to return Human Review "
            "without compatible mammogram report findings."
        ),
    }


def main() -> None:
    result = audit()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(json.dumps({
        "rows": result["rows"],
        "classification_counts": result["classification_counts"],
        "binary_field_missing_counts": result["binary_field_missing_counts"],
        "complete_age_signs_symptoms_rows": result["complete_age_signs_symptoms_rows"],
        "complete_case_class_counts": result["complete_case_class_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()

