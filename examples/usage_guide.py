"""Generate a usage guide document for docscriptor."""

from __future__ import annotations

import base64
from pathlib import Path

from docscriptor import (
    BulletList,
    Citation,
    CitationSource,
    Chapter,
    CodeBlock,
    Document,
    Figure,
    FigureList,
    FigureReference,
    NumberedList,
    Paragraph,
    ParagraphStyle,
    ReferencesPage,
    Section,
    Strong,
    Subsection,
    Subsubsection,
    Table,
    TableList,
    TableReference,
    markup,
    styled,
)


OUTPUT_DIR = Path("artifacts") / "usage-guide"
SAMPLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0tcAAAAASUVORK5CYII="
)

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

CUSTOM_BLOCK_SNIPPET = """from docscriptor import Paragraph, ParagraphStyle, Strong


class WarningParagraph(Paragraph):
    def __init__(self, *content):
        super().__init__(
            Strong("Warning: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )
"""


class NoteParagraph(Paragraph):
    """Simple reusable paragraph used inside the guide itself."""

    def __init__(self, *content: object) -> None:
        super().__init__(
            Strong("Note: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )


def _write_sample_image(path: Path) -> None:
    path.write_bytes(SAMPLE_PNG)


def build_usage_guide_document(output_dir: Path) -> Document:
    """Build the in-memory usage guide document."""

    figure_path = output_dir / "usage-guide-figure.png"
    _write_sample_image(figure_path)

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
                    Strong("Document"),
                    ", ",
                    Strong("Chapter"),
                    ", ",
                    Strong("Section"),
                    ", and ",
                    Strong("Paragraph"),
                    ". Use helper functions only where they transform content, such as inline styling or markup parsing.",
                ),
                Paragraph(
                    "The default theme uses Times New Roman body text and progressively stronger chapter and section styling so the hierarchy stays visible in both DOCX and PDF output."
                ),
                Paragraph(
                    "See ",
                    TableReference("primitive-summary"),
                    " for the core block inventory and ",
                    FigureReference("hierarchy-overview"),
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
                Table(
                    identifier="primitive-summary",
                    headers=["Kind", "Examples", "Purpose"],
                    rows=[
                        ["Hierarchy", "Chapter, Section, Subsection, Subsubsection", "Document structure"],
                        ["Blocks", "Paragraph, BulletList, NumberedList, CodeBlock, Table, Figure", "Content layout"],
                        ["Inline", "Text, Strong, Emphasis, Code", "Inline emphasis"],
                        ["Helpers", "markup, styled", "Inline authoring shortcuts"],
                    ],
                    caption="Core authoring primitives.",
                    column_widths=[1.6, 3.1, 1.8],
                ),
                Paragraph(
                    "The rendering matrix in ",
                    TableReference("workflow-output"),
                    " complements the structural summary with output-oriented guidance.",
                ),
                Subsection(
                    "Hierarchy Depth",
                    Paragraph(
                        "Use ",
                        Strong("Chapter"),
                        " for the largest division, then step down through ",
                        Strong("Section"),
                        ", ",
                        Strong("Subsection"),
                        ", and ",
                        Strong("Subsubsection"),
                        " as the document becomes more specific.",
                    ),
                    Figure(
                        figure_path,
                        identifier="hierarchy-overview",
                        caption="Heading hierarchy example output.",
                        width_inches=1.4,
                    ),
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
                    FigureReference("rendering-preview"),
                    " together with ",
                    TableReference("workflow-output"),
                    " when comparing delivery formats."
                ),
                Table(
                    identifier="workflow-output",
                    headers=["Goal", "Preferred Output"],
                    rows=[
                        ["Editable review", "DOCX"],
                        ["Stable distribution", "PDF"],
                    ],
                    caption="Rendering outputs by goal.",
                    column_widths=[2.4, 2.6],
                ),
                Figure(
                    figure_path,
                    identifier="rendering-preview",
                    caption="Repeated figure rendering example.",
                    width_inches=1.8,
                ),
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
                    Citation("pydocs-repository"),
                    "."
                ),
                TableList(),
                FigureList(),
            ),
        ),
        ReferencesPage(),
        author="docscriptor examples",
        summary="Usage guide document",
        citations=[
            CitationSource(
                key="pydocs-repository",
                organization="Gonie-Gonie",
                title="pydocs",
                publisher="GitHub repository",
                year="2026",
                url="https://github.com/Gonie-Gonie/pydocs",
            )
        ],
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
