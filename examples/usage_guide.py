"""Generate a usage guide document for docscriptor."""

from __future__ import annotations

from pathlib import Path

from docscriptor import (
    Chapter,
    CodeBlock,
    Document,
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


GUIDE_DOCUMENT = Document(
    "Using docscriptor",
    Chapter(
        "Getting Started",
        Section(
            "Quick Start",
            Paragraph(
                "Build a document tree with Python objects and render the same structure to ",
                styled("DOCX", color="#004C99", bold=True),
                " and ",
                styled("PDF", color="#8A1C1C", bold=True),
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
                ". Use helper functions only where they add behavior, such as list creation or inline markup.",
            ),
            numbered_list(
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
                headers=["Kind", "Examples", "Purpose"],
                rows=[
                    ["Hierarchy", "Chapter, Section, Subsection, Subsubsection", "Document structure"],
                    ["Blocks", "Paragraph, CodeBlock, Table, Figure", "Content layout"],
                    ["Inline", "Text, Strong, Emphasis, Code", "Inline emphasis"],
                    ["Helpers", "bullet_list, numbered_list, markup", "Faster authoring"],
                ],
                caption="Table 1. Core authoring primitives.",
                column_widths=[1.6, 3.1, 1.8],
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
                Subsubsection(
                    "When To Use CodeBlock",
                    bullet_list(
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
                "A practical workflow is to keep the document definition in Python, generate outputs in CI, and review the resulting files where needed."
            ),
            bullet_list(
                "Use DOCX when you want editable handoff files.",
                "Use PDF when you want stable distribution output.",
                "Keep examples in version control so the API stays exercised.",
            ),
        ),
    ),
    author="docscriptor examples",
    summary="Usage guide document",
)


def build_usage_guide(output_dir: str | Path) -> tuple[Path, Path]:
    """Build the usage guide and export it to DOCX and PDF."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    docx_path = output_path / "docscriptor-usage-guide.docx"
    pdf_path = output_path / "docscriptor-usage-guide.pdf"
    GUIDE_DOCUMENT.save_docx(docx_path)
    GUIDE_DOCUMENT.save_pdf(pdf_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the guide into the default example output directory."""

    docx_path, pdf_path = build_usage_guide(OUTPUT_DIR)
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
