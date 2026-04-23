"""Generate a usage guide document for docscriptor."""

from __future__ import annotations

from pathlib import Path
import struct
import zlib

from docscriptor import (
    Bold,
    Box,
    BoxStyle,
    BulletList,
    CitationSource,
    Chapter,
    CommentsPage,
    CodeBlock,
    Document,
    Equation,
    Figure,
    FigureList,
    HeadingNumbering,
    ListStyle,
    Monospace,
    NumberedList,
    Paragraph,
    ParagraphStyle,
    ReferencesPage,
    Section,
    Subsection,
    Subsubsection,
    Table,
    TableOfContents,
    TableList,
    Theme,
    cite,
    comment,
    math,
    markup,
    styled,
)


OUTPUT_DIR = Path("artifacts") / "usage-guide"
RELATED_WORK_BIBTEX = """@article{knuth1984literate,
  author = {Donald E. Knuth},
  title = {Literate Programming},
  journal = {The Computer Journal},
  volume = {27},
  number = {2},
  pages = {97--111},
  year = {1984},
  publisher = {Oxford University Press},
  url = {https://doi.org/10.1093/comjnl/27.2.97}
}"""

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

ADVANCED_API_SNIPPET = """from docscriptor import (
    Body,
    CitationLibrary,
    CitationSource,
    CommentsPage,
    Document,
    DocscriptorError,
    Equation,
    Paragraph,
    ParagraphStyle,
    TableOfContents,
    Text,
    TextStyle,
    Theme,
    __version__,
    cite,
    comment,
    math,
    md,
    styled,
)

library = CitationLibrary([CitationSource("Usage Guide", key="guide", year="2026")])
theme = Theme(contents_title="Contents", show_page_numbers=True, page_number_format="Page {page}")

doc = Document(
    f"API Notes for {__version__}",
    body=Body(
        TableOfContents(),
        Paragraph(
            Text("Intro: ", style=TextStyle(bold=True)),
            styled("styled text", color="#005A87"),
            " and ",
            *md("**markdown** helpers"),
            " plus ",
            comment("review notes", "Portable comments can also be collected on a comments page."),
            " and ",
            math(r"\\alpha^2 + \\beta^2 = \\gamma^2"),
            ".",
            style=ParagraphStyle(space_after=14),
        ),
        Equation(r"\\int_0^1 x^2 \\, dx = \\frac{1}{3}"),
        Paragraph("Reference source ", cite("guide"), "."),
        CommentsPage(),
    ),
    theme=theme,
    citations=library,
)

try:
    doc.save_docx("artifacts/api-notes.docx")
except DocscriptorError as exc:
    print(exc)
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


class UsageGuideTables:
    def __init__(
        self,
        *,
        primitive_summary: Table,
        workflow_output: Table,
        structure_reference: Table,
        block_reference: Table,
        generated_reference: Table,
        inline_reference: Table,
        citation_reference: Table,
        method_reference: Table,
    ) -> None:
        self.primitive_summary = primitive_summary
        self.workflow_output = workflow_output
        self.structure_reference = structure_reference
        self.block_reference = block_reference
        self.generated_reference = generated_reference
        self.inline_reference = inline_reference
        self.citation_reference = citation_reference
        self.method_reference = method_reference


class UsageGuideFigures:
    def __init__(self, *, hierarchy_overview: Figure, rendering_preview: Figure) -> None:
        self.hierarchy_overview = hierarchy_overview
        self.rendering_preview = rendering_preview


def _api_reference_row(name: str, signature: str, purpose: str) -> list[Paragraph]:
    return [
        Paragraph(Bold(name)),
        Paragraph(Monospace(signature)),
        Paragraph(purpose),
    ]


def _method_reference_row(member: str, purpose: str) -> list[Paragraph]:
    return [
        Paragraph(Monospace(member)),
        Paragraph(purpose),
    ]


def _reference_table(
    *,
    caption: str,
    rows: list[list[Paragraph]],
    column_widths: list[float],
    headers: list[str] | None = None,
) -> Table:
    return Table(
        headers=headers or ["API", "Signature", "Purpose"],
        rows=rows,
        caption=caption,
        column_widths=column_widths,
    )


def _build_usage_guide_tables() -> UsageGuideTables:
    structure_rows = [
        _api_reference_row(
            "Document",
            "Document(title, *children, body=None, author=None, summary=None, theme=None, citations=None)",
            "Root document. Accept positional blocks or body=Body(...), then render with save_docx() or save_pdf().",
        ),
        _api_reference_row(
            "Body",
            "Body(*children)",
            "Optional explicit block container when you want to assemble the document body separately.",
        ),
        _api_reference_row(
            "Chapter",
            "Chapter(title, *children)",
            "First-level division used for the largest sections in the document.",
        ),
        _api_reference_row(
            "Section",
            "Section(title, *children, level=2)",
            "General titled container for nested blocks when you need a custom section level.",
        ),
        _api_reference_row(
            "Subsection",
            "Subsection(title, *children)",
            "Third-level section for more detailed structure.",
        ),
        _api_reference_row(
            "Subsubsection",
            "Subsubsection(title, *children)",
            "Fourth-level section for compact nested topics or reference notes.",
        ),
    ]
    block_rows = [
        _api_reference_row(
            "Paragraph",
            "Paragraph(*content, style=None)",
            "Standard prose block built from strings, Text fragments, or inline helper output.",
        ),
        _api_reference_row(
            "BulletList",
            "BulletList(*items)",
            "Unordered list. Each item is normalized into a Paragraph automatically.",
        ),
        _api_reference_row(
            "NumberedList",
            "NumberedList(*items)",
            "Ordered list for sequences, procedures, or ranked steps.",
        ),
        _api_reference_row(
            "CodeBlock",
            "CodeBlock(code, language=None, style=ParagraphStyle(...))",
            "Preformatted code snippet that keeps indentation intact in DOCX and PDF.",
        ),
        _api_reference_row(
            "Box",
            "Box(*children, title=None, style=None)",
            "Bordered container for paragraphs, lists, tables, figures, and other authored blocks when the layout should stay visually grouped.",
        ),
        _api_reference_row(
            "Equation",
            "Equation(expression, style=ParagraphStyle(alignment='center', ...))",
            "Centered block equation using lightweight LaTeX-style input shared by both renderers.",
        ),
        _api_reference_row(
            "Table",
            "Table(headers, rows, caption=None, column_widths=None, identifier=None)",
            "Grid-style text table. Captioned tables are numbered and added to TableList.",
        ),
        _api_reference_row(
            "Figure",
            "Figure(image_path, caption=None, width_inches=None, identifier=None)",
            "Image block. Captioned figures are numbered and added to FigureList.",
        ),
    ]
    generated_rows = [
        _api_reference_row(
            "TableOfContents",
            "TableOfContents(title=None)",
            "Generated outline of chapter and section headings in document order.",
        ),
        _api_reference_row(
            "TableList",
            "TableList(title=None)",
            "Generated list of captioned tables with their numbers.",
        ),
        _api_reference_row(
            "FigureList",
            "FigureList(title=None)",
            "Generated list of captioned figures with their numbers.",
        ),
        _api_reference_row(
            "CommentsPage",
            "CommentsPage(title=None)",
            "Generated page collecting numbered comments encountered in the document.",
        ),
        _api_reference_row(
            "ReferencesPage",
            "ReferencesPage(title=None)",
            "Generated references page containing only cited bibliography entries.",
        ),
    ]
    inline_rows = [
        _api_reference_row(
            "Text",
            "Text(value, style=TextStyle())",
            "Base inline fragment for plain text with optional style overrides.",
        ),
        _api_reference_row(
            "Bold",
            "Bold(value, style=None)",
            "Inline text fragment with bold emphasis.",
        ),
        _api_reference_row(
            "Italic",
            "Italic(value, style=None)",
            "Inline text fragment with italic emphasis.",
        ),
        _api_reference_row(
            "Monospace",
            "Monospace(value, style=None)",
            "Inline code-style fragment using the monospace theme font.",
        ),
        _api_reference_row(
            "Comment",
            "Comment(value, *comment, author=None, initials=None, style=None)",
            "Inline text with a numbered portable comment marker and optional DOCX comment metadata.",
        ),
        _api_reference_row(
            "Math",
            "Math(value, style=None)",
            "Inline math fragment written in lightweight LaTeX syntax.",
        ),
        _api_reference_row(
            "TextStyle",
            "TextStyle(font_name=None, font_size=None, color=None, bold=None, italic=None, underline=None)",
            "Low-level inline style values used by Text and the helper functions.",
        ),
        _api_reference_row(
            "ParagraphStyle",
            "ParagraphStyle(alignment='left', space_after=12.0, leading=None)",
            "Paragraph-level alignment and spacing configuration.",
        ),
        _api_reference_row(
            "BoxStyle",
            "BoxStyle(border_color='B7C2D0', background_color='F7FAFC', ...)",
            "Visual styling for Box, including border, fill, and padding defaults shared by DOCX and PDF renderers.",
        ),
        _api_reference_row(
            "HeadingNumbering",
            "HeadingNumbering(enabled=True, formats=('decimal', ...), separator='.', ...)",
            "Controls default chapter and section numbering such as 1, 1.1, and 1.1.1.",
        ),
        _api_reference_row(
            "ListStyle",
            "ListStyle(marker_format='decimal', bullet='•', prefix='', suffix='.', ...)",
            "Configures bullet and ordered-list markers, numbering style, and indentation.",
        ),
        _api_reference_row(
            "Theme",
            "Theme(body_font_name='Times New Roman', monospace_font_name='Courier New', ...)",
            "Document-wide renderer defaults for fonts, labels, heading numbering, list markers, and generated section titles.",
        ),
        _api_reference_row(
            "styled",
            "styled(value, **style_values)",
            "Convenience helper that returns Text with a TextStyle created from keyword arguments.",
        ),
        _api_reference_row(
            "math",
            "math(value, style=None)",
            "Convenience helper that returns an inline Math fragment from a LaTeX-like expression.",
        ),
    ]
    citation_rows = [
        _api_reference_row(
            "CitationSource",
            "CitationSource(title, key=None, authors=(), organization=None, publisher=None, year=None, url=None, note=None)",
            "In-memory bibliography entry that can be cited directly or registered under a key.",
        ),
        _api_reference_row(
            "CitationLibrary",
            "CitationLibrary(entries=None)",
            "Registry of CitationSource objects addressable by citation key.",
        ),
        _api_reference_row(
            "cite",
            "cite(target, style=None)",
            "Create an inline citation from a CitationSource instance or a registered citation key.",
        ),
        _api_reference_row(
            "comment",
            "comment(value, *note, author=None, initials=None, style=None)",
            "Create inline text with a numbered portable comment that can also populate CommentsPage.",
        ),
        _api_reference_row(
            "markup",
            "markup(source, style=None)",
            "Parse **bold**, *italic*, and `code` fragments into Text objects.",
        ),
        _api_reference_row(
            "md",
            "md(source, style=None)",
            "Short alias for markup() when you prefer a terse name in authoring code.",
        ),
        _api_reference_row(
            "__version__",
            "__version__",
            "Package version string exported from docscriptor at the module level.",
        ),
        _api_reference_row(
            "DocscriptorError",
            "DocscriptorError",
            "Raised when document structure, citations, or rendering inputs cannot be resolved safely.",
        ),
    ]
    method_rows = [
        _method_reference_row("Document.save_docx(path)", "Render the current Document to a DOCX file and return the output path."),
        _method_reference_row("Document.save_pdf(path)", "Render the current Document to a PDF file and return the output path."),
        _method_reference_row("Text.plain_text()", "Return the raw text value for a single inline fragment."),
        _method_reference_row("Math.plain_text()", "Return a readable plain-text representation of a lightweight LaTeX expression."),
        _method_reference_row("Paragraph.plain_text()", "Join paragraph content into plain text without styling metadata."),
        _method_reference_row("Equation.plain_text()", "Return a readable plain-text representation of the block equation."),
        _method_reference_row("Section.plain_title()", "Return a plain-text version of a heading title."),
        _method_reference_row("TextStyle.merged(*others)", "Overlay later inline styles on top of earlier ones."),
        _method_reference_row("HeadingNumbering.format_label(counters)", "Render the configured hierarchical heading label from a sequence of counters."),
        _method_reference_row("ListStyle.marker_for(index)", "Return the rendered bullet or ordered-list marker for a zero-based item index."),
        _method_reference_row("Theme.heading_size(level)", "Return the configured font size for a heading level."),
        _method_reference_row("Theme.heading_emphasis(level)", "Return the (bold, italic) emphasis tuple for a heading level."),
        _method_reference_row("Theme.heading_alignment(level)", "Return the alignment used for the given heading level."),
        _method_reference_row("Theme.format_heading_label(counters)", "Render the heading numbering label that should precede a chapter or section title."),
        _method_reference_row("Theme.list_style(ordered=...)", "Return the default ListStyle used for bullet or ordered lists."),
        _method_reference_row("Theme.format_page_number(page_number)", "Render the configured footer page number string for a page."),
        _method_reference_row("CitationSource.format_reference()", "Format a bibliography entry for the generated references page."),
        _method_reference_row("CitationLibrary.add(entry)", "Register a keyed citation source inside the library."),
        _method_reference_row("CitationLibrary.resolve(key)", "Look up a citation source by key."),
        _method_reference_row("CitationLibrary.from_bibtex(source)", "Create a citation library from BibTeX text."),
    ]

    return UsageGuideTables(
        primitive_summary=Table(
            headers=["Kind", "Examples", "Purpose"],
            rows=[
                ["Hierarchy", "Chapter, Section, Subsection, Subsubsection", "Document structure"],
                ["Blocks", "Paragraph, BulletList, NumberedList, CodeBlock, Equation, Table, Figure", "Content layout"],
                ["Inline", "Text, Bold, Italic, Monospace, Comment, Math", "Inline emphasis"],
                ["Helpers", "markup, styled, cite, comment, math", "Authoring shortcuts"],
            ],
            caption="Core authoring primitives.",
            column_widths=[1.6, 3.1, 1.8],
        ),
        workflow_output=Table(
            headers=["Goal", "Preferred Output"],
            rows=[
                ["Editable review", "DOCX"],
                ["Stable distribution", "PDF"],
            ],
            caption="Rendering outputs by goal.",
            column_widths=[2.4, 2.6],
        ),
        structure_reference=_reference_table(
            caption="Structural document objects.",
            rows=structure_rows,
            column_widths=[1.3, 3.6, 1.7],
        ),
        block_reference=_reference_table(
            caption="Content block objects.",
            rows=block_rows,
            column_widths=[1.3, 3.6, 1.7],
        ),
        generated_reference=_reference_table(
            caption="Generated document blocks.",
            rows=generated_rows,
            column_widths=[1.6, 3.3, 1.7],
        ),
        inline_reference=_reference_table(
            caption="Inline styling primitives.",
            rows=inline_rows,
            column_widths=[1.4, 3.5, 1.7],
        ),
        citation_reference=_reference_table(
            caption="Citations, markup, and module helpers.",
            rows=citation_rows,
            column_widths=[1.6, 3.3, 1.7],
        ),
        method_reference=_reference_table(
            caption="Key public methods.",
            headers=["Method", "Purpose"],
            rows=method_rows,
            column_widths=[3.0, 4.0],
        ),
    )


def _build_usage_guide_figures(figure_path: Path) -> UsageGuideFigures:
    return UsageGuideFigures(
        hierarchy_overview=Figure(
            figure_path,
            caption="Heading hierarchy example output.",
            width_inches=1.4,
        ),
        rendering_preview=Figure(
            figure_path,
            caption="Repeated figure rendering example.",
            width_inches=1.8,
        ),
    )


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
    tables = _build_usage_guide_tables()
    figures = _build_usage_guide_figures(figure_path)

    document = Document(
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
                        Bold("Chapter"),
                        " for the largest division, then step down through ",
                        Bold("Section"),
                        ", ",
                        Bold("Subsection"),
                        ", and ",
                        Bold("Subsubsection"),
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
                    " when comparing delivery formats."
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
                    cite(repository_source),
                    "."
                ),
                Paragraph(
                    "That Python-first style also overlaps with the literate-programming tradition described in ",
                    cite("knuth1984literate"),
                    ", where source structure and explanation stay tightly connected.",
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
            ),
        ),
        Chapter(
            "API Reference",
            Section(
                "Document and Structure",
                Paragraph(
                    "This chapter turns the guide into a compact API reference: every stable name exported from ",
                    Monospace("docscriptor"),
                    " is listed in the tables below so the example can double as working documentation.",
                ),
                Paragraph(
                    "Use ",
                    tables.structure_reference,
                    " as the entry point. ",
                    Bold("Document"),
                    " accepts either positional blocks or ",
                    Monospace("body=Body(...)"),
                    ", so teams can pre-build sections before rendering."
                ),
                tables.structure_reference,
                Paragraph(
                    "In practice, ",
                    Bold("Chapter"),
                    ", ",
                    Bold("Section"),
                    ", ",
                    Bold("Subsection"),
                    ", and ",
                    Bold("Subsubsection"),
                    " cover most authored hierarchy, while ",
                    Bold("Section"),
                    " remains available when you need explicit control over the heading level."
                ),
            ),
            Section(
                "Blocks and Generated Pages",
                Paragraph(
                    "The primary content blocks are ",
                    Bold("Paragraph"),
                    ", ",
                    Bold("BulletList"),
                    ", ",
                    Bold("NumberedList"),
                    ", ",
                    Bold("CodeBlock"),
                    ", ",
                    Bold("Equation"),
                    ", ",
                    Bold("Table"),
                    ", and ",
                    Bold("Figure"),
                    ". Generated companions such as ",
                    Bold("TableOfContents"),
                    ", ",
                    Bold("TableList"),
                    ", ",
                    Bold("FigureList"),
                    ", ",
                    Bold("CommentsPage"),
                    ", and ",
                    Bold("ReferencesPage"),
                    " stay synchronized with the same source tree.",
                ),
                Paragraph(
                    "Use ",
                    tables.block_reference,
                    " for authored blocks and ",
                    tables.generated_reference,
                    " for generated blocks. Captioned tables and figures participate in numbering automatically."
                ),
                tables.block_reference,
                tables.generated_reference,
            ),
            Section(
                "Text, Style, and Theme",
                Paragraph(
                    "For inline content, compose paragraphs from ",
                    Bold("Text"),
                    ", ",
                    Bold("Bold"),
                    ", ",
                    Bold("Italic"),
                    ", ",
                    Bold("Monospace"),
                    ", ",
                    Bold("Comment"),
                    ", ",
                    Bold("Math"),
                    ", and ",
                    Bold("styled"),
                    ". Use ",
                    Bold("TextStyle"),
                    " for fragment-level styling and ",
                    Bold("ParagraphStyle"),
                    " for alignment or spacing."
                ),
                Paragraph(
                    "Theme configuration stays centralized in ",
                    Bold("Theme"),
                    ", whose heading helpers ",
                    Monospace("heading_size"),
                    ", ",
                    Monospace("heading_emphasis"),
                    ", and ",
                    Monospace("heading_alignment"),
                    " control renderer defaults. The same theme also controls footer page numbers through ",
                    Monospace("show_page_numbers"),
                    ", ",
                    Monospace("page_number_alignment"),
                    ", and ",
                    Monospace("page_number_format"),
                    ". Numbered headings default to values such as ",
                    Monospace("1"),
                    ", ",
                    Monospace("1.1"),
                    ", and ",
                    Monospace("1.1.1"),
                    " through ",
                    Bold("HeadingNumbering"),
                    ", while ",
                    Bold("ListStyle"),
                    " controls bullet and ordered-list markers."
                ),
                tables.inline_reference,
                NoteParagraph(
                    "If you prefer markdown-like authoring over explicit fragments, ",
                    markup("`markup()` and `md()` produce the same kind of inline Text objects."),
                ),
                Paragraph(
                    "For visually grouped content such as warnings, review notes, or side calculations, use ",
                    Bold("Box"),
                    " together with ",
                    Bold("BoxStyle"),
                    " to keep related blocks inside a single bordered container."
                ),
                Paragraph(
                    "Portable comments such as ",
                    comment("review note", "DOCX output adds a native Word comment and both renderers can list it on a comments page."),
                    " can travel with the document, and inline math such as ",
                    math(r"\alpha^2 + \beta^2 = \gamma^2"),
                    " stays readable without leaving Python."
                ),
                Equation(r"\int_0^1 \alpha x^2 \, dx = \frac{\alpha}{3}"),
            ),
            Section(
                "Citations, Helpers, and Errors",
                Paragraph(
                    "Use ",
                    Bold("CitationSource"),
                    " and ",
                    Bold("CitationLibrary"),
                    " when you want bibliography data to live in Python, or pass BibTeX text directly to ",
                    Bold("Document"),
                    "(",
                    Monospace("citations=..."),
                    ") when you already have existing reference metadata."
                ),
                Paragraph(
                    "At the module level, ",
                    Monospace("__version__"),
                    " exposes the package version string, and ",
                    Bold("DocscriptorError"),
                    " identifies citation or structure problems that should fail fast during rendering."
                ),
                tables.citation_reference,
                CodeBlock(ADVANCED_API_SNIPPET, language="python"),
            ),
            Section(
                "Public Methods",
                Paragraph(
                    "The constructors above cover object creation; ",
                    tables.method_reference,
                    " lists the key helper methods that you are most likely to call directly from application code."
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
                    " act as the quick lookup index for the stable public surface."
                ),
            ),
        ),
        CommentsPage(),
        ReferencesPage(),
        author="docscriptor examples",
        summary="Usage guide document",
        theme=Theme(show_page_numbers=True, page_number_format="Page {page}"),
        citations=RELATED_WORK_BIBTEX,
    )
    return document


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
    document = build_usage_guide_document(OUTPUT_DIR)
    docx_path = OUTPUT_DIR / "docscriptor-usage-guide.docx"
    pdf_path = OUTPUT_DIR / "docscriptor-usage-guide.pdf"
    document.save_docx(docx_path)
    document.save_pdf(pdf_path)
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
