"""Code snippets embedded into the usage guide example."""

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
