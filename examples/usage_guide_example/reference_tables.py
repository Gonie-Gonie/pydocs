"""Reference tables and figures used by the usage guide example."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docscriptor import Figure, Paragraph, Table, Text


@dataclass(slots=True)
class UsageGuideTables:
    """Grouped table objects used repeatedly across the guide."""

    primitive_summary: Table
    workflow_output: Table
    structure_reference: Table
    block_reference: Table
    generated_reference: Table
    inline_reference: Table
    citation_reference: Table
    method_reference: Table


@dataclass(slots=True)
class UsageGuideFigures:
    """Grouped figure objects used repeatedly across the guide."""

    hierarchy_overview: Figure
    rendering_preview: Figure


def _api_reference_row(name: str, signature: str, purpose: str) -> list[Paragraph]:
    return [
        Paragraph(Text.bold(name)),
        Paragraph(Text.code(signature)),
        Paragraph(purpose),
    ]


def _method_reference_row(member: str, purpose: str) -> list[Paragraph]:
    return [
        Paragraph(Text.code(member)),
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


def build_usage_guide_tables() -> UsageGuideTables:
    """Build the table set used by the usage guide document."""

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
            "Table(headers_or_dataframe, rows=None, caption=None, column_widths=None, identifier=None, style=None, include_index=False)",
            "Grid-style table. Accept explicit rows or dataframe-like objects directly, and captioned tables are numbered and added to TableList.",
        ),
        _api_reference_row(
            "TableCell",
            "TableCell(value, colspan=1, rowspan=1, background_color=None)",
            "Single table cell object used when you need explicit multicolumn or multirow spans.",
        ),
        _api_reference_row(
            "TableStyle",
            "TableStyle(header_background_color='E8EDF5', border_color='B7C2D0', ...)",
            "Renderer-neutral table styling for header fill, borders, row banding, and padding.",
        ),
        _api_reference_row(
            "Figure",
            "Figure(image_source, caption=None, width_inches=None, identifier=None, format='png', dpi=150)",
            "Image block that accepts a filesystem path or a savefig()-compatible figure object. Captioned figures are numbered and added to FigureList.",
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
            "FootnotesPage",
            "FootnotesPage(title=None)",
            "Generated page collecting numbered portable footnotes encountered in the document.",
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
            "Footnote",
            "Footnote(value, *note, style=None)",
            "Inline text with a numbered portable footnote marker collected into FootnotesPage.",
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
            "footnote",
            "footnote(value, *note, style=None)",
            "Create inline text with a numbered portable footnote that can also populate FootnotesPage.",
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
        _method_reference_row(
            "Document.save_docx(path)",
            "Render the current Document to a DOCX file and return the output path.",
        ),
        _method_reference_row(
            "Document.save_pdf(path)",
            "Render the current Document to a PDF file and return the output path.",
        ),
        _method_reference_row(
            "Text.plain_text()",
            "Return the raw text value for a single inline fragment.",
        ),
        _method_reference_row(
            "Math.plain_text()",
            "Return a readable plain-text representation of a lightweight LaTeX expression.",
        ),
        _method_reference_row(
            "Paragraph.plain_text()",
            "Join paragraph content into plain text without styling metadata.",
        ),
        _method_reference_row(
            "Equation.plain_text()",
            "Return a readable plain-text representation of the block equation.",
        ),
        _method_reference_row(
            "Section.plain_title()",
            "Return a plain-text version of a heading title.",
        ),
        _method_reference_row(
            "Table.from_dataframe(dataframe, ...)",
            "Create a Table directly from a dataframe-like object while preserving column metadata.",
        ),
        _method_reference_row(
            "TextStyle.merged(*others)",
            "Overlay later inline styles on top of earlier ones.",
        ),
        _method_reference_row(
            "HeadingNumbering.format_label(counters)",
            "Render the configured hierarchical heading label from a sequence of counters.",
        ),
        _method_reference_row(
            "ListStyle.marker_for(index)",
            "Return the rendered bullet or ordered-list marker for a zero-based item index.",
        ),
        _method_reference_row(
            "Theme.heading_size(level)",
            "Return the configured font size for a heading level.",
        ),
        _method_reference_row(
            "Theme.heading_emphasis(level)",
            "Return the (bold, italic) emphasis tuple for a heading level.",
        ),
        _method_reference_row(
            "Theme.heading_alignment(level)",
            "Return the alignment used for the given heading level.",
        ),
        _method_reference_row(
            "Theme.format_heading_label(counters)",
            "Render the heading numbering label that should precede a chapter or section title.",
        ),
        _method_reference_row(
            "Theme.list_style(ordered=...)",
            "Return the default ListStyle used for bullet or ordered lists.",
        ),
        _method_reference_row(
            "Theme.format_page_number(page_number)",
            "Render the configured footer page number string for a page.",
        ),
        _method_reference_row(
            "CitationSource.format_reference()",
            "Format a bibliography entry for the generated references page.",
        ),
        _method_reference_row(
            "CitationLibrary.add(entry)",
            "Register a keyed citation source inside the library.",
        ),
        _method_reference_row(
            "CitationLibrary.resolve(key)",
            "Look up a citation source by key.",
        ),
        _method_reference_row(
            "CitationLibrary.from_bibtex(source)",
            "Create a citation library from BibTeX text.",
        ),
    ]

    return UsageGuideTables(
        primitive_summary=Table(
            headers=["Kind", "Examples", "Purpose"],
            rows=[
                [
                    "Hierarchy",
                    "Chapter, Section, Subsection, Subsubsection",
                    "Document structure",
                ],
                [
                    "Blocks",
                    "Paragraph, BulletList, NumberedList, CodeBlock, Equation, Table, Figure",
                    "Content layout",
                ],
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


def build_usage_guide_figures(figure_path: Path) -> UsageGuideFigures:
    """Build the figure set used by the usage guide document."""

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
