from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Inches


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "final_report.md"
OUT = ROOT / "final_submission_assets" / "report" / "A股多因子量化交易系统课程报告.docx"


def add_markdown_table(document: Document, lines: list[str]) -> None:
    rows = []
    for line in lines:
        parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(part) <= {"-", ":"} for part in parts):
            continue
        rows.append(parts)
    if not rows:
        return
    table = document.add_table(rows=1, cols=len(rows[0]))
    table.style = "Table Grid"
    for i, cell in enumerate(rows[0]):
        table.rows[0].cells[i].text = cell
    for row in rows[1:]:
        cells = table.add_row().cells
        for i, cell in enumerate(row[: len(cells)]):
            cells[i].text = cell


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    document.core_properties.title = "A股多因子量化交易系统课程报告"

    lines = REPORT.read_text(encoding="utf-8").splitlines()
    table_buffer: list[str] = []

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            add_markdown_table(document, table_buffer)
            table_buffer = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            table_buffer.append(line)
            continue
        flush_table()
        if not line:
            continue
        if line.startswith("# "):
            document.add_heading(line[2:].strip(), level=0)
        elif line.startswith("## "):
            document.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            document.add_heading(line[4:].strip(), level=2)
        elif line.startswith("![") and "](" in line and line.endswith(")"):
            alt = line[2 : line.index("]")]
            rel = line[line.index("(") + 1 : -1]
            image_path = (REPORT.parent / rel).resolve()
            if image_path.exists():
                document.add_paragraph(alt)
                document.add_picture(str(image_path), width=Inches(6.2))
        elif line.startswith("```"):
            continue
        else:
            document.add_paragraph(line)
    flush_table()
    document.save(OUT)


if __name__ == "__main__":
    main()
