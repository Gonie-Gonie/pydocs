from __future__ import annotations

import base64
from pathlib import Path

import docscriptor
from docx import Document as WordDocument
from pypdf import PdfReader

from docscriptor import (
    Chapter,
    Code,
    CodeBlock,
    Document,
    Emphasis,
    Figure,
    ListBlock,
    Paragraph,
    ParagraphStyle,
    Section,
    Strong,
    Subsection,
    Subsubsection,
    Table,
    bullet_list,
    markup,
    numbered_list,
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


def test_list_helpers_create_block_instances() -> None:
    bullet = bullet_list("first", Paragraph("second"))
    ordered = numbered_list("step one", "step two")

    assert isinstance(bullet, ListBlock)
    assert bullet.ordered is False
    assert [item.plain_text() for item in bullet.items] == ["first", "second"]
    assert ordered.ordered is True
    assert [item.plain_text() for item in ordered.items] == ["step one", "step two"]


def test_heading_hierarchy_uses_latex_like_levels() -> None:
    chapter = Chapter(
        "Part I",
        Section(
            "Overview",
            Subsection(
                "Details",
                Subsubsection("Examples"),
            ),
        ),
    )

    assert chapter.level == 1
    assert chapter.children[0].level == 2
    assert chapter.children[0].children[0].level == 3
    assert chapter.children[0].children[0].children[0].level == 4


def test_public_api_prefers_classes_for_structural_nodes() -> None:
    assert hasattr(docscriptor, "Document")
    assert hasattr(docscriptor, "Chapter")
    assert hasattr(docscriptor, "Section")
    assert hasattr(docscriptor, "Paragraph")
    assert hasattr(docscriptor, "Table")
    assert hasattr(docscriptor, "Figure")

    for removed_name in (
        "document",
        "body",
        "chapter",
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "code_block",
        "table",
        "figure",
    ):
        assert not hasattr(docscriptor, removed_name)


def test_document_renders_to_docx_and_pdf(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    _write_sample_image(image_path)

    document = Document(
        "Pipeline Report",
        Chapter(
            "Summary",
            Section(
                "Highlights",
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
                    bullet_list(
                        "Lists render into both DOCX and PDF.",
                        Paragraph("Paragraph instances can also be list items."),
                    ),
                    Subsubsection(
                        "Export Steps",
                        CodeBlock(
                            "from docscriptor import Document\n\ndocument.save_docx('report.docx')\ndocument.save_pdf('report.pdf')",
                            language="python",
                        ),
                    ),
                    numbered_list("Create the model", "Render the files"),
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
    assert "Highlights" in paragraph_texts
    assert "Artifacts" in paragraph_texts
    assert "Export Steps" in paragraph_texts
    assert any("docscriptor" in text for text in paragraph_texts)
    assert any("Figure 1. Tiny sample image." in text for text in paragraph_texts)
    assert any("from docscriptor import Document" in text for text in paragraph_texts)
    assert any(paragraph.style.name == "List Bullet" for paragraph in word_document.paragraphs)
    assert any(paragraph.style.name == "List Number" for paragraph in word_document.paragraphs)

    assert len(word_document.tables) == 1
    assert word_document.tables[0].cell(1, 0).text == "DOCX"
    assert word_document.tables[0].cell(2, 1).text == "generated"

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Pipeline Report" in pdf_text
    assert "Summary" in pdf_text
    assert "Highlights" in pdf_text
    assert "Artifacts" in pdf_text
    assert "Export Steps" in pdf_text
    assert "Table 1. Generated artifacts." in pdf_text
    assert "Figure 1. Tiny sample image." in pdf_text
    assert "Lists render into both DOCX and PDF." in pdf_text
    assert "from docscriptor import Document" in pdf_text
