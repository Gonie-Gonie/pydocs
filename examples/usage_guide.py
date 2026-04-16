"""Generate a usage guide document for docscriptor."""

from __future__ import annotations

from pathlib import Path
import struct
import zlib

from docscriptor import (
    Bold,
    BulletList,
    CitationSource,
    Chapter,
    CodeBlock,
    Document,
    Figure,
    FigureList,
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


OUTPUT_DIR = Path("artifacts") / "usage-guide"

QUICK_START_SNIPPET = """from docscriptor import Chapter, Document, Paragraph, Section

doc = Document(
    "Hello docscriptor",
    Chapter(
        "Getting Started",
        Section(
            "Summary",
            Paragraph("This document was defined with Python objects."),
        ),
    ),
)

doc.save_docx("artifacts/hello.docx")
doc.save_pdf("artifacts/hello.pdf")
"""

CUSTOM_BLOCK_SNIPPET = """from docscriptor import Bold, Paragraph, ParagraphStyle


class WarningParagraph(Paragraph):
    def __init__(self, *content):
        super().__init__(
            Bold("Warning: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )
"""


class NoteParagraph(Paragraph):
    """Simple reusable paragraph used inside the guide itself."""

    def __init__(self, *content: object) -> None:
        super().__init__(
            Bold("Note: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )


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


def build_usage_guide_document(output_dir: Path) -> Document:
    """Build the in-memory usage guide document."""

    figure_path = output_dir / "usage-guide-figure.png"
    _write_sample_image(figure_path)

    repository_source = CitationSource(
        "pydocs",
        organization="Gonie-Gonie",
        publisher="GitHub repository",
        year="2026",
        url="https://github.com/Gonie-Gonie/pydocs",
    )
    primitive_summary_table = Table(
        headers=["Kind", "Examples", "Purpose"],
        rows=[
            ["Hierarchy", "Chapter, Section, Subsection, Subsubsection", "Document structure"],
            ["Blocks", "Paragraph, BulletList, NumberedList, CodeBlock, Table, Figure", "Content layout"],
            ["Inline", "Text, Bold, Italic, Monospace", "Inline emphasis"],
            ["Helpers", "markup, styled, cite", "Authoring shortcuts"],
        ],
        caption="Core authoring primitives.",
        column_widths=[1.6, 3.1, 1.8],
    )
    hierarchy_overview_figure = Figure(
        figure_path,
        caption="Heading hierarchy example output.",
        width_inches=1.4,
    )
    workflow_output_table = Table(
        headers=["Goal", "Preferred Output"],
        rows=[
            ["Editable review", "DOCX"],
            ["Stable distribution", "PDF"],
        ],
        caption="Rendering outputs by goal.",
        column_widths=[2.4, 2.6],
    )
    rendering_preview_figure = Figure(
        figure_path,
        caption="Repeated figure rendering example.",
        width_inches=1.8,
    )

    return Document(
        "Using docscriptor",
        Chapter(
            "Getting Started",
            Section(
                "Quick Start",
                Paragraph(
                    "Build a document tree with Python objects and render the same structure to ",
                    styled("DOCX", bold=True),
                    " and ",
                    styled("PDF", bold=True),
                    ".",
                    style=ParagraphStyle(space_after=14),
                ),
                Paragraph(
                    "Instantiate structural nodes directly with classes such as ",
                    Bold("Document"),
                    ", ",
                    Bold("Chapter"),
                    ", ",
                    Bold("Section"),
                    ", and ",
                    Bold("Paragraph"),
                    ". Use helper functions only where they transform content, such as inline styling or markup parsing.",
                ),
                Paragraph(
                    "The default theme uses Times New Roman body text and progressively stronger chapter and section styling so the hierarchy stays visible in both DOCX and PDF output."
                ),
                Paragraph(
                    "See ",
                    primitive_summary_table,
                    " for the core block inventory and ",
                    hierarchy_overview_figure,
                    " for a compact figure example that can be cited from prose.",
                ),
                NumberedList(
                    "Import the model objects you need.",
                    "Compose chapters, sections, and paragraphs as regular Python instances.",
                    "Call save_docx() and save_pdf() on the document.",
                ),
                CodeBlock(QUICK_START_SNIPPET, language="python"),
                NoteParagraph(
                    "Inline helpers such as ",
                    markup("**bold** text, *italic* text, and `code` fragments"),
                    " still work inside normal paragraphs.",
                ),
            ),
        ),
        Chapter(
            "Authoring Model",
            Section(
                "Core Building Blocks",
                Paragraph(
                    "The current model mixes heading classes, block objects, inline fragments, and a small set of authoring helpers so documents stay easy to read in plain Python."
                ),
                primitive_summary_table,
                Paragraph(
                    "The rendering matrix in ",
                    workflow_output_table,
                    " complements the structural summary with output-oriented guidance.",
                ),
                Subsection(
                    "Hierarchy Depth",
                    Paragraph(
                        "Use ",
                        Bold("Chapter"),
                        " for the largest division, then step down through ",
                        Bold("Section"),
                        ", ",
                        Bold("Subsection"),
                        ", and ",
                        Bold("Subsubsection"),
                        " as the document becomes more specific.",
                    ),
                    hierarchy_overview_figure,
                    Subsubsection(
                        "When To Use CodeBlock",
                        BulletList(
                            "Show a complete example without losing indentation.",
                            "Document reusable templates and helper classes.",
                            "Keep prose and code snippets inside the same generated guide.",
                        ),
                    ),
                ),
            ),
            Section(
                "Reusable Abstractions",
                Paragraph(
                    "Because the model is class-based, teams can wrap common patterns in their own subclasses instead of repeating styling rules."
                ),
                CodeBlock(CUSTOM_BLOCK_SNIPPET, language="python"),
                Paragraph(
                    "That pattern works especially well for recurring notices, report sections, or company-specific templates."
                ),
            ),
            Section(
                "Rendering Workflow",
                Paragraph(
                    "Use ",
                    rendering_preview_figure,
                    " together with ",
                    workflow_output_table,
                    " when comparing delivery formats."
                ),
                workflow_output_table,
                rendering_preview_figure,
                BulletList(
                    "Use DOCX when you want editable handoff files.",
                    "Use PDF when you want stable distribution output.",
                    "Keep examples in version control so the API stays exercised.",
                ),
            ),
            Section(
                "Generated Lists",
                Paragraph(
                    "Generated lists are derived from captioned figures and tables, so uncaptured objects stay out of the numbering sequence."
                ),
                Paragraph(
                    "The project repository itself can be cited inline, as shown by ",
                    cite(repository_source),
                    "."
                ),
                Paragraph(
                    "For existing BibTeX data, pass a bibliography string to ",
                    Bold("Document"),
                    " and call ",
                    Bold("cite"),
                    "(",
                    Monospace('"some-key"'),
                    ") when you want key-based lookup.",
                ),
                TableList(),
                FigureList(),
            ),
        ),
        ReferencesPage(),
        author="docscriptor examples",
        summary="Usage guide document",
    )


def build_usage_guide(output_dir: str | Path) -> tuple[Path, Path]:
    """Build the usage guide and export it to DOCX and PDF."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document = build_usage_guide_document(output_path)
    docx_path = output_path / "docscriptor-usage-guide.docx"
    pdf_path = output_path / "docscriptor-usage-guide.pdf"
    document.save_docx(docx_path)
    document.save_pdf(pdf_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the guide into the default example output directory."""

    docx_path, pdf_path = build_usage_guide(OUTPUT_DIR)
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
