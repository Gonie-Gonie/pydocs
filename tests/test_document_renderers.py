from __future__ import annotations

from pathlib import Path
import struct
import zlib

import docscriptor
from docx import Document as WordDocument
from docx.shared import RGBColor
from pypdf import PdfReader

from docscriptor import (
    Bold,
    BulletList,
    CitationSource,
    Chapter,
    CodeBlock,
    Document,
    Figure,
    FigureList,
    Italic,
    Monospace,
    NumberedList,
    Paragraph,
    ParagraphStyle,
    ReferencesPage,
    Section,
    Subsection,
    Subsubsection,
    Table,
    TableList,
    cite,
    markup,
    styled,
)

class HighlightedParagraph(Paragraph):
    pass


def _write_sample_image(path: Path) -> None:
    path.write_bytes(_build_sample_png())


def _build_sample_png(width: int = 360, height: int = 220) -> bytes:
    rows: list[bytes] = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            if y < 34:
                pixel = (34, 58, 94)
            elif x < 18 or x >= width - 18 or y < 52 or y >= height - 18:
                pixel = (214, 221, 233)
            elif 26 < x < width - 26 and 70 < y < 102:
                pixel = (205, 121, 62)
            elif (x - 36) // 54 % 2 == 0 and 122 < y < 182:
                pixel = (89, 132, 198)
            else:
                pixel = (247, 249, 252)
            row.extend(pixel)
        rows.append(bytes(row))

    raw_image = b"".join(rows)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw_image, level=9)),
            _png_chunk(b"IEND", b""),
        )
    )


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    payload = chunk_type + data
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", checksum)


def _pdf_font_names(pdf_path: Path) -> set[str]:
    font_names: set[str] = set()
    for page in PdfReader(str(pdf_path)).pages:
        resources = page.get("/Resources")
        if resources is None or "/Font" not in resources:
            continue
        fonts = resources["/Font"].get_object()
        for font in fonts.values():
            font_object = font.get_object()
            base_font = font_object.get("/BaseFont")
            if base_font is not None:
                font_names.add(str(base_font))
    return font_names


def _pdf_image_draw_count(pdf_path: Path) -> int:
    count = 0
    for page in PdfReader(str(pdf_path)).pages:
        resources = page.get("/Resources")
        if resources is None or "/XObject" not in resources:
            continue
        xobjects = resources["/XObject"].get_object()
        image_names = {
            name
            for name, xobject in xobjects.items()
            if xobject.get_object().get("/Subtype") == "/Image"
        }
        if not image_names:
            continue
        content = page.get_contents()
        if content is None:
            continue
        content_bytes = content.get_data()
        for name in image_names:
            token = f"{name} Do".encode()
            count += content_bytes.count(token)
    return count


def _pdf_content_bytes(pdf_path: Path) -> bytes:
    parts: list[bytes] = []
    for page in PdfReader(str(pdf_path)).pages:
        contents = page.get_contents()
        if contents is None:
            continue
        if isinstance(contents, list):
            for item in contents:
                parts.append(item.get_data())
        else:
            parts.append(contents.get_data())
    return b"\n".join(parts)


def test_version_is_defined() -> None:
    from docscriptor import __version__

    assert __version__ == "0.1.0"


def test_markup_creates_styled_fragments() -> None:
    fragments = markup("plain **bold** *italic* `code`")

    assert [fragment.value for fragment in fragments] == ["plain ", "bold", " ", "italic", " ", "code"]
    assert fragments[1].style.bold is True
    assert fragments[3].style.italic is True
    assert fragments[5].style.font_name == "Courier New"


def test_list_classes_create_block_instances() -> None:
    bullet = BulletList("first", Paragraph("second"))
    ordered = NumberedList("step one", "step two")

    assert isinstance(bullet, BulletList)
    assert bullet.ordered is False
    assert [item.plain_text() for item in bullet.items] == ["first", "second"]
    assert isinstance(ordered, NumberedList)
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
    assert hasattr(docscriptor, "BulletList")
    assert hasattr(docscriptor, "NumberedList")
    assert hasattr(docscriptor, "TableList")
    assert hasattr(docscriptor, "FigureList")
    assert hasattr(docscriptor, "cite")
    assert hasattr(docscriptor, "Bold")
    assert hasattr(docscriptor, "Italic")
    assert hasattr(docscriptor, "Monospace")
    assert hasattr(docscriptor, "Table")
    assert hasattr(docscriptor, "Figure")
    assert not hasattr(docscriptor, "ListBlock")
    assert not hasattr(docscriptor, "Citation")
    assert not hasattr(docscriptor, "TableReference")
    assert not hasattr(docscriptor, "FigureReference")
    assert not hasattr(docscriptor, "Strong")
    assert not hasattr(docscriptor, "Emphasis")
    assert not hasattr(docscriptor, "Code")

    for removed_name in (
        "document",
        "body",
        "chapter",
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "code_block",
        "bullet_list",
        "numbered_list",
        "table",
        "figure",
    ):
        assert not hasattr(docscriptor, removed_name)


def test_bibtex_string_creates_citation_library() -> None:
    document = Document(
        "Bibliography Test",
        Paragraph("Example"),
        citations="""@misc{pydocs-repository,
  title = {pydocs},
  organization = {Gonie-Gonie},
  year = {2026},
  url = {https://github.com/Gonie-Gonie/pydocs},
  note = {GitHub repository}
}""",
    )

    entry = document.citations.resolve("pydocs-repository")
    assert entry.title == "pydocs"
    assert entry.organization == "Gonie-Gonie"
    assert entry.url == "https://github.com/Gonie-Gonie/pydocs"
    assert "GitHub repository" in entry.format_reference()


def test_document_renders_to_docx_and_pdf(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    _write_sample_image(image_path)
    repository_source = CitationSource(
        "pydocs",
        organization="Gonie-Gonie",
        publisher="GitHub repository",
        year="2026",
        url="https://github.com/Gonie-Gonie/pydocs",
    )
    registered_source = CitationSource(
        "Release Notes",
        key="release-notes",
        organization="Gonie-Gonie",
        publisher="Documentation index",
        year="2026",
        url="https://github.com/Gonie-Gonie/pydocs/releases",
    )
    unused_source = CitationSource(
        "Internal Draft",
        key="internal-draft",
        organization="Gonie-Gonie",
        year="2026",
        url="https://example.invalid/internal-draft",
    )
    artifacts_table = Table(
        headers=["Type", "Status"],
        rows=[
            ["DOCX", "generated"],
            ["PDF", "generated"],
        ],
        caption="Generated artifacts.",
        column_widths=[2.5, 2.5],
    )
    workflow_table = Table(
        headers=["Step", "Target"],
        rows=[
            ["Draft review", "DOCX"],
            ["Release", "PDF"],
        ],
        caption="Output workflow.",
        column_widths=[2.5, 2.5],
    )
    preview_figure = Figure(
        image_path,
        caption=Paragraph("Tiny sample image."),
        width_inches=1.0,
    )
    preview_figure_second = Figure(
        image_path,
        caption=Paragraph("Second tiny sample image."),
        width_inches=1.2,
    )

    document = Document(
        "Pipeline Report",
        Chapter(
            "Summary",
            Section(
                "Highlights",
                HighlightedParagraph(
                    "The ",
                    Bold("docscriptor"),
                    " pipeline supports ",
                    Italic("styled"),
                    " text, ",
                    Monospace("code"),
                    ", and ",
                    styled("custom color", color="#0066AA", bold=True),
                    ".",
                    style=ParagraphStyle(space_after=14),
                ),
                Paragraph(markup("Inline helpers also support **bold** and *italic* markup.")),
                Paragraph(
                    "See ",
                    artifacts_table,
                    " and ",
                    preview_figure,
                    " for the generated outputs.",
                ),
                Paragraph(
                    "Repository status is tracked in ",
                    cite(repository_source),
                    ".",
                ),
                Paragraph(
                    "Registered bibliography entries can still be cited as ",
                    cite("release-notes"),
                    ".",
                ),
                Subsection(
                    "Artifacts",
                    BulletList(
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
                    NumberedList("Create the model", "Render the files"),
                    artifacts_table,
                    workflow_table,
                    preview_figure,
                    preview_figure_second,
                    TableList(),
                    FigureList(),
                ),
            ),
        ),
        ReferencesPage(),
        author="pytest",
        summary="Renderer integration test",
        citations=[registered_source, unused_source],
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
    assert "List of Tables" in paragraph_texts
    assert "List of Figures" in paragraph_texts
    assert "References" in paragraph_texts
    assert any("docscriptor" in text for text in paragraph_texts)
    assert any("See Table 1 and Figure 1 for the generated outputs." in text for text in paragraph_texts)
    assert any("Repository status is tracked in [1]." in text for text in paragraph_texts)
    assert any("Registered bibliography entries can still be cited as [2]." in text for text in paragraph_texts)
    assert paragraph_texts.count("Table 1. Generated artifacts.") >= 2
    assert paragraph_texts.count("Table 2. Output workflow.") >= 2
    assert paragraph_texts.count("Figure 1. Tiny sample image.") >= 2
    assert paragraph_texts.count("Figure 2. Second tiny sample image.") >= 2
    assert any("https://github.com/Gonie-Gonie/pydocs" in text for text in paragraph_texts)
    assert any("https://github.com/Gonie-Gonie/pydocs/releases" in text for text in paragraph_texts)
    assert all("internal-draft" not in text.lower() for text in paragraph_texts)
    assert any("from docscriptor import Document" in text for text in paragraph_texts)
    assert any(paragraph.style.name == "List Bullet" for paragraph in word_document.paragraphs)
    assert any(paragraph.style.name == "List Number" for paragraph in word_document.paragraphs)
    assert len(word_document.inline_shapes) == 2

    assert len(word_document.tables) == 2
    assert word_document.tables[0].cell(1, 0).text == "DOCX"
    assert word_document.tables[0].cell(2, 1).text == "generated"
    assert word_document.tables[1].cell(1, 0).text == "Draft review"
    assert word_document.tables[1].cell(2, 1).text == "PDF"
    assert word_document.styles["Normal"].font.name == "Times New Roman"
    assert word_document.styles["Title"].font.name == "Times New Roman"
    assert word_document.styles["Heading 1"].font.name == "Times New Roman"
    assert word_document.styles["Heading 2"].font.name == "Times New Roman"
    assert word_document.styles["Heading 3"].font.name == "Times New Roman"
    assert word_document.styles["Heading 4"].font.name == "Times New Roman"
    assert word_document.styles["Title"].font.color.rgb == RGBColor(0, 0, 0)
    assert word_document.styles["Heading 1"].font.color.rgb == RGBColor(0, 0, 0)
    assert word_document.styles["Heading 2"].font.color.rgb == RGBColor(0, 0, 0)
    assert word_document.styles["Heading 3"].font.color.rgb == RGBColor(0, 0, 0)
    assert word_document.styles["Heading 4"].font.color.rgb == RGBColor(0, 0, 0)

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Pipeline Report" in pdf_text
    assert "Summary" in pdf_text
    assert "Highlights" in pdf_text
    assert "Artifacts" in pdf_text
    assert "Export Steps" in pdf_text
    assert "See Table 1 and Figure 1 for the generated outputs." in pdf_text
    assert "Repository status is tracked in [1]." in pdf_text
    assert "Registered bibliography entries can still be cited as [2]." in pdf_text
    assert pdf_text.count("Table 1. Generated artifacts.") >= 2
    assert pdf_text.count("Table 2. Output workflow.") >= 2
    assert pdf_text.count("Figure 1. Tiny sample image.") >= 2
    assert pdf_text.count("Figure 2. Second tiny sample image.") >= 2
    assert "List of Tables" in pdf_text
    assert "List of Figures" in pdf_text
    assert "References" in pdf_text
    assert "https://github.com/Gonie-Gonie/pydocs" in pdf_text
    assert "https://github.com/Gonie-Gonie/pydocs/releases" in pdf_text
    assert "Internal Draft" not in pdf_text
    assert "Lists render into both DOCX and PDF." in pdf_text
    assert "from docscriptor import Document" in pdf_text
    assert "1\nLists render into both DOCX and PDF." not in pdf_text
    assert "1\nCreate the model" in pdf_text
    assert _pdf_image_draw_count(pdf_path) == 2
    pdf_fonts = _pdf_font_names(pdf_path)
    assert "/Times-Roman" in pdf_fonts
    assert "/Times-Bold" in pdf_fonts
    assert pdf_fonts & {"/Times-BoldItalic", "/Times-Italic"}
    pdf_content = _pdf_content_bytes(pdf_path)
    assert b"18 Tf" in pdf_content
    assert b"15 Tf" in pdf_content
    assert b"13 Tf" in pdf_content
    assert b"11.5 Tf" in pdf_content
