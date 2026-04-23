"""Build the package-style usage guide example for docscriptor."""

from __future__ import annotations

from pathlib import Path

from docscriptor import (
    BulletList,
    Chapter,
    Comment,
    CommentsPage,
    CodeBlock,
    Document,
    Equation,
    FigureList,
    Footnote,
    FootnotesPage,
    HeadingNumbering,
    ListStyle,
    Math,
    NumberedList,
    Paragraph,
    ParagraphStyle,
    ReferencesPage,
    Section,
    Subsection,
    Subsubsection,
    TableList,
    TableOfContents,
    Text,
    Theme,
)
from examples.usage_guide_example.assets import copy_usage_guide_figure
from examples.usage_guide_example.citations import (
    build_related_work_library,
    build_repository_source,
)
from examples.usage_guide_example.reference_tables import (
    build_usage_guide_figures,
    build_usage_guide_tables,
)
from examples.usage_guide_example.snippets import (
    ADVANCED_API_SNIPPET,
    CUSTOM_BLOCK_SNIPPET,
    QUICK_START_SNIPPET,
)


OUTPUT_DIR = Path("artifacts") / "usage-guide"


class NoteParagraph(Paragraph):
    """Simple reusable paragraph used inside the guide itself."""

    def __init__(self, *content: object) -> None:
        super().__init__(
            Text.bold("Note: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )


def build_usage_guide_document(output_dir: Path) -> Document:
    """Build the in-memory usage guide document."""

    figure_path = copy_usage_guide_figure(output_dir)
    repository_source = build_repository_source()
    related_work_library = build_related_work_library()
    tables = build_usage_guide_tables()
    figures = build_usage_guide_figures(figure_path)

    return Document(
        "Using docscriptor",
        TableList(),
        FigureList(),
        TableOfContents(),
        Chapter(
            "Getting Started",
            Section(
                "Quick Start",
                Paragraph(
                    "Build a document tree with Python objects and render the same structure to ",
                    Text.styled("DOCX", bold=True),
                    " and ",
                    Text.styled("PDF", bold=True),
                    ".",
                    style=ParagraphStyle(space_after=14),
                ),
                Paragraph(
                    "Instantiate structural nodes directly with classes such as ",
                    Text.bold("Document"),
                    ", ",
                    Text.bold("Chapter"),
                    ", ",
                    Text.bold("Section"),
                    ", and ",
                    Text.bold("Paragraph"),
                    ". Use helper functions only where they transform content, such as inline styling or markup parsing.",
                ),
                Paragraph(
                    "The default theme uses Times New Roman body text and progressively stronger chapter and section styling so the hierarchy stays visible in both DOCX and PDF output."
                ),
                Paragraph(
                    "See ",
                    tables.primitive_summary,
                    " for the core block inventory and ",
                    figures.hierarchy_overview,
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
                    Text.from_markup("**bold** text, *italic* text, and `code` fragments"),
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
                tables.primitive_summary,
                Paragraph(
                    "The rendering matrix in ",
                    tables.workflow_output,
                    " complements the structural summary with output-oriented guidance.",
                ),
                Subsection(
                    "Hierarchy Depth",
                    Paragraph(
                        "Use ",
                        Text.bold("Chapter"),
                        " for the largest division, then step down through ",
                        Text.bold("Section"),
                        ", ",
                        Text.bold("Subsection"),
                        ", and ",
                        Text.bold("Subsubsection"),
                        " as the document becomes more specific.",
                    ),
                    figures.hierarchy_overview,
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
                    figures.rendering_preview,
                    " together with ",
                    tables.workflow_output,
                    " when comparing delivery formats.",
                ),
                tables.workflow_output,
                figures.rendering_preview,
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
                    repository_source.cite(),
                    ".",
                ),
                Paragraph(
                    "That Python-first style also overlaps with the literate-programming tradition described in ",
                    related_work_library.cite("knuth1984literate"),
                    ", where source structure and explanation stay tightly connected.",
                ),
                Paragraph(
                    "For existing BibTeX data, pass a bibliography string to ",
                    Text.bold("Document"),
                    " and call ",
                    Text.bold("cite"),
                    "(",
                    Text.code('"some-key"'),
                    ") when you want key-based lookup.",
                ),
            ),
        ),
        Chapter(
            "API Reference",
            Section(
                "Document and Structure",
                Paragraph(
                    "This chapter turns the guide into a compact API reference: every stable name exported from ",
                    Text.code("docscriptor"),
                    " is listed in the tables below so the example can double as working documentation.",
                ),
                Paragraph(
                    "Use ",
                    tables.structure_reference,
                    " as the entry point. ",
                    Text.bold("Document"),
                    " accepts either positional blocks or ",
                    Text.code("body=Body(...)"),
                    ", so teams can pre-build sections before rendering.",
                ),
                tables.structure_reference,
                Paragraph(
                    "In practice, ",
                    Text.bold("Chapter"),
                    ", ",
                    Text.bold("Section"),
                    ", ",
                    Text.bold("Subsection"),
                    ", and ",
                    Text.bold("Subsubsection"),
                    " cover most authored hierarchy, while ",
                    Text.bold("Section"),
                    " remains available when you need explicit control over the heading level.",
                ),
            ),
            Section(
                "Blocks and Generated Pages",
                Paragraph(
                    "The primary content blocks are ",
                    Text.bold("Paragraph"),
                    ", ",
                    Text.bold("BulletList"),
                    ", ",
                    Text.bold("NumberedList"),
                    ", ",
                    Text.bold("CodeBlock"),
                    ", ",
                    Text.bold("Equation"),
                    ", ",
                    Text.bold("Table"),
                    ", and ",
                    Text.bold("Figure"),
                    ". Generated companions such as ",
                    Text.bold("TableOfContents"),
                    ", ",
                    Text.bold("TableList"),
                    ", ",
                    Text.bold("FigureList"),
                    ", ",
                    Text.bold("CommentsPage"),
                    ", and ",
                    Text.bold("ReferencesPage"),
                    " stay synchronized with the same source tree.",
                ),
                Paragraph(
                    "Use ",
                    tables.block_reference,
                    " for authored blocks and ",
                    tables.generated_reference,
                    " for generated blocks. Captioned tables and figures participate in numbering automatically, ",
                    Text.bold("Table"),
                    " can be built directly from dataframe-like objects, and ",
                    Text.bold("Figure"),
                    " can render savefig()-compatible figure objects without a temporary file.",
                ),
                tables.block_reference,
                tables.generated_reference,
            ),
            Section(
                "Text, Style, and Theme",
                Paragraph(
                    "For inline content, compose paragraphs from ",
                    Text.bold("Text"),
                    ", ",
                    Text.bold("Bold"),
                    ", ",
                    Text.bold("Italic"),
                    ", ",
                    Text.bold("Monospace"),
                    ", ",
                    Text.bold("Comment"),
                    ", ",
                    Text.bold("Math"),
                    ", and ",
                    Text.bold("styled"),
                    ". Use ",
                    Text.bold("TextStyle"),
                    " for fragment-level styling and ",
                    Text.bold("ParagraphStyle"),
                    " for alignment or spacing.",
                ),
                Paragraph(
                    "Theme configuration stays centralized in ",
                    Text.bold("Theme"),
                    ", whose heading helpers ",
                    Text.code("heading_size"),
                    ", ",
                    Text.code("heading_emphasis"),
                    ", and ",
                    Text.code("heading_alignment"),
                    " control renderer defaults. The same theme also controls footer page numbers through ",
                    Text.code("show_page_numbers"),
                    ", ",
                    Text.code("page_number_alignment"),
                    ", and ",
                    Text.code("page_number_format"),
                    ". Numbered headings default to values such as ",
                    Text.code("1"),
                    ", ",
                    Text.code("1.1"),
                    ", and ",
                    Text.code("1.1.1"),
                    " through ",
                    Text.bold("HeadingNumbering"),
                    ", while ",
                    Text.bold("ListStyle"),
                    " controls bullet and ordered-list markers.",
                ),
                tables.inline_reference,
                NoteParagraph(
                    "If you prefer markdown-like authoring over explicit fragments, ",
                    Text.from_markup("`markup()` and `md()` produce the same kind of inline Text objects."),
                ),
                Paragraph(
                    "For visually grouped content such as warnings, review notes, or side calculations, use ",
                    Text.bold("Box"),
                    " together with ",
                    Text.bold("BoxStyle"),
                    " to keep related blocks inside a single bordered container.",
                ),
                Paragraph(
                    "Portable comments such as ",
                    Comment.annotated(
                        "review note",
                        "DOCX output adds a native Word comment and both renderers can list it on a comments page.",
                    ),
                    ", footnotes such as ",
                    Footnote.annotated(
                        "term",
                        "Portable footnotes are collected on a generated footnotes page for stable DOCX/PDF output.",
                    ),
                    " can travel with the document, and inline math such as ",
                    Math.inline(r"\alpha^2 + \beta^2 = \gamma^2"),
                    " stays readable without leaving Python.",
                ),
                Equation(r"\int_0^1 \alpha x^2 \, dx = \frac{\alpha}{3}"),
            ),
            Section(
                "Citations, Helpers, and Errors",
                Paragraph(
                    "Use ",
                    Text.bold("CitationSource"),
                    " and ",
                    Text.bold("CitationLibrary"),
                    " when you want bibliography data to live in Python, or pass BibTeX text directly to ",
                    Text.bold("Document"),
                    "(",
                    Text.code("citations=..."),
                    ") when you already have existing reference metadata.",
                ),
                Paragraph(
                    "At the module level, ",
                    Text.code("__version__"),
                    " exposes the package version string, and ",
                    Text.bold("DocscriptorError"),
                    " identifies citation or structure problems that should fail fast during rendering.",
                ),
                tables.citation_reference,
                CodeBlock(ADVANCED_API_SNIPPET, language="python"),
            ),
            Section(
                "Public Methods",
                Paragraph(
                    "The constructors above cover object creation; ",
                    tables.method_reference,
                    " lists the key helper methods that you are most likely to call directly from application code.",
                ),
                tables.method_reference,
                Paragraph(
                    "Together, ",
                    tables.structure_reference,
                    ", ",
                    tables.block_reference,
                    ", ",
                    tables.generated_reference,
                    ", ",
                    tables.inline_reference,
                    ", ",
                    tables.citation_reference,
                    ", and ",
                    tables.method_reference,
                    " act as the quick lookup index for the stable public surface.",
                ),
            ),
        ),
        FootnotesPage(),
        CommentsPage(),
        ReferencesPage(),
        author="docscriptor examples",
        summary="Usage guide document",
        theme=Theme(
            show_page_numbers=True,
            page_number_format="Page {page}",
            heading_numbering=HeadingNumbering(),
            bullet_list_style=ListStyle(marker_format="bullet", bullet="\u2022", suffix=""),
        ),
        citations=related_work_library,
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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    docx_path, pdf_path = build_usage_guide(OUTPUT_DIR)
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
