from __future__ import annotations

import base64
from pathlib import Path

from docx import Document as WordDocument
from pypdf import PdfReader

from docscriptor import (
    Code,
    Document,
    Emphasis,
    Figure,
    Paragraph,
    ParagraphStyle,
    Section,
    Strong,
    Subsection,
    Table,
    markup,
    styled,
)


SAMPLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0tcAAAAASUVORK5CYII="
)


class HighlightedParagraph(Paragraph):
    pass


def _write_sample_image(path: Path) -> None:
    path.write_bytes(SAMPLE_PNG)


def test_version_is_defined() -> None:
    from docscriptor import __version__

    assert __version__ == "0.1.0"


def test_markup_creates_styled_fragments() -> None:
    fragments = markup("plain **bold** *italic* `code`")

    assert [fragment.value for fragment in fragments] == ["plain ", "bold", " ", "italic", " ", "code"]
    assert fragments[1].style.bold is True
    assert fragments[3].style.italic is True
    assert fragments[5].style.font_name == "Courier"


def test_document_renders_to_docx_and_pdf(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    _write_sample_image(image_path)

    document = Document(
        "Pipeline Report",
        Section(
            "Summary",
            HighlightedParagraph(
                "The ",
                Strong("docscriptor"),
                " pipeline supports ",
                Emphasis("styled"),
                " text, ",
                Code("code"),
                ", and ",
                styled("custom color", color="#0066AA", bold=True),
                ".",
                style=ParagraphStyle(space_after=14),
            ),
            Paragraph(markup("Inline helpers also support **bold** and *italic* markup.")),
            Subsection(
                "Artifacts",
                Table(
                    headers=["Type", "Status"],
                    rows=[
                        ["DOCX", "generated"],
                        ["PDF", "generated"],
                    ],
                    caption="Table 1. Generated artifacts.",
                    column_widths=[2.5, 2.5],
                ),
                Figure(image_path, caption=Paragraph("Figure 1. Tiny sample image."), width_inches=1.0),
            ),
        ),
        author="pytest",
        summary="Renderer integration test",
    )

    docx_path = tmp_path / "report.docx"
    pdf_path = tmp_path / "report.pdf"

    document.save_docx(docx_path)
    document.save_pdf(pdf_path)

    assert docx_path.exists()
    assert pdf_path.exists()
    assert docx_path.stat().st_size > 0
    assert pdf_path.stat().st_size > 0

    word_document = WordDocument(docx_path)
    paragraph_texts = [paragraph.text for paragraph in word_document.paragraphs]
    assert "Pipeline Report" in paragraph_texts
    assert "Summary" in paragraph_texts
    assert any("docscriptor" in text for text in paragraph_texts)
    assert any("Figure 1. Tiny sample image." in text for text in paragraph_texts)

    assert len(word_document.tables) == 1
    assert word_document.tables[0].cell(1, 0).text == "DOCX"
    assert word_document.tables[0].cell(2, 1).text == "generated"

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Pipeline Report" in pdf_text
    assert "Summary" in pdf_text
    assert "Table 1. Generated artifacts." in pdf_text
    assert "Figure 1. Tiny sample image." in pdf_text
