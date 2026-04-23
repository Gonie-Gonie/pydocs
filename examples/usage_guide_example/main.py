"""Standalone usage guide example for docscriptor.

This file intentionally keeps almost all of the document assembly in one place.
The goal is not only to build a detailed guide, but also to let a new user read
the Python source and immediately see how the document tree maps to the output.
"""

from __future__ import annotations

from pathlib import Path

from docscriptor import (
    Box,
    BoxStyle,
    BulletList,
    Chapter,
    CitationLibrary,
    CitationSource,
    Comment,
    CommentsPage,
    CodeBlock,
    Document,
    Equation,
    Figure,
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
    Table,
    TableCell,
    TableList,
    TableOfContents,
    Text,
    Theme,
    bold,
    code,
    color,
    italic,
    link,
)


OUTPUT_DIR = Path("artifacts") / "usage-guide"
EXAMPLE_DIR = Path(__file__).resolve().parent
ASSET_DIR = EXAMPLE_DIR / "assets"
FIGURE_PATH = ASSET_DIR / "usage-guide-figure.png"

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

report = Document(
    "Hello docscriptor",
    Chapter(
        "Getting Started",
        Section(
            "Overview",
            Paragraph("This document was defined with Python objects."),
        ),
    ),
)

report.save_docx("artifacts/hello.docx")
report.save_pdf("artifacts/hello.pdf")
"""

NUMBERING_SNIPPET = """from docscriptor import HeadingNumbering, ListStyle, Paragraph, Section, Theme

theme = Theme(
    heading_numbering=HeadingNumbering(
        formats=("decimal", "decimal", "lower-alpha"),
    ),
    numbered_list_style=ListStyle(
        marker_format="upper-roman",
        prefix="(",
        suffix=")",
    ),
)

abstract = Section(
    "Abstract",
    Paragraph("Article-style front matter can be left unnumbered."),
    level=2,
    numbered=False,
)
"""

DATA_INTEGRATION_SNIPPET = """import pandas as pd
import matplotlib.pyplot as plt
from docscriptor import Figure, Paragraph, Table

results = pd.read_csv("assets/results.csv")
results_table = Table.from_dataframe(
    results,
    caption="Results loaded directly from a CSV file.",
)

figure, axis = plt.subplots()
axis.plot(results["step"], results["score"])
results_plot = Figure(
    figure,
    caption=Paragraph("Plot generated directly from matplotlib."),
)
"""

PROJECT_LAYOUT_SNIPPET = """my-report/
  main.py
  assets/
    architecture.png
    team-photo.png
  data/
    results.csv
    ablation.csv
  artifacts/
    report.docx
    report.pdf
"""


def build_usage_guide_document() -> Document:
    """Build a detailed usage guide while keeping the code easy to follow."""

    related_work = CitationLibrary.from_bibtex(RELATED_WORK_BIBTEX)
    repository_source = CitationSource(
        "docscriptor repository",
        organization="Gonie-Gonie",
        publisher="GitHub repository",
        year="2026",
        url="https://github.com/Gonie-Gonie/pydocs",
    )

    rendering_outputs_table = Table(
        headers=["Goal", "Preferred Output", "Why"],
        rows=[
            ["Editable review", "DOCX", "Works well for tracked changes and collaborator edits."],
            ["Stable distribution", "PDF", "Preserves layout for export and submission."],
            ["One source of truth", "Both", "The same document tree can render to both outputs."],
        ],
        caption="Rendering goals and output formats.",
        column_widths=[1.8, 1.5, 3.0],
    )
    core_objects_table = Table(
        headers=["Layer", "Objects", "Role"],
        rows=[
            ["Structure", "Document, Chapter, Section, Paragraph", "Define the document tree directly in Python."],
            ["Content", "BulletList, NumberedList, CodeBlock, Box, Table, Figure", "Insert readable block-level content."],
            ["Inline actions", "bold, italic, code, styled, Comment.annotated, Footnote.annotated", "Apply emphasis and annotations explicitly where text is authored."],
        ],
        caption="Core authoring objects by responsibility.",
        column_widths=[1.5, 3.2, 2.0],
    )
    generated_pages_table = Table(
        headers=["Generated page", "What triggers it", "Why it matters"],
        rows=[
            ["TableOfContents", "Add TableOfContents()", "Render a contents page from authored headings."],
            ["TableList / FigureList", "Add TableList() or FigureList()", "Collect captioned tables and figures automatically."],
            [
                "FootnotesPage",
                Paragraph(
                    "Add FootnotesPage() to collect portable notes ",
                    Footnote.annotated(
                        "including table-cell notes",
                        "This footnote was created from a table cell inside the usage guide.",
                    ),
                    ".",
                ),
                "Keeps footnotes stable in both DOCX and PDF.",
            ],
            ["CommentsPage", "Add CommentsPage()", "Exports inline review comments to a dedicated page."],
            ["ReferencesPage", "Add ReferencesPage()", "Only cited bibliography entries are rendered."],
        ],
        caption="Generated pages available in a document.",
        column_widths=[1.6, 2.6, 2.2],
    )
    numbering_table = Table(
        headers=["Target", "Default", "Customize with"],
        rows=[
            ["Heading labels", "1 / 1.1 / 1.1.1", "Theme(heading_numbering=HeadingNumbering(...))"],
            ["Ordered lists", "1. 2. 3.", "ListStyle(marker_format=..., prefix=..., suffix=...)"],
            ["Unnumbered headings", "Disabled by default", "Section(..., numbered=False)"],
        ],
        caption="Default numbering behavior and customization hooks.",
        column_widths=[1.5, 1.8, 3.3],
    )
    table_layout_table = Table(
        headers=[
            [TableCell("Feature", rowspan=2), TableCell("Simple Use", colspan=2)],
            ["Common", "Advanced"],
        ],
        rows=[
            ["Headers", "headers=['A', 'B']", "headers=[[TableCell('Metrics', colspan=2)], ['Latency', 'Quality']]"],
            ["Cells", "plain strings or Paragraph(...)", "TableCell(..., rowspan=2) and TableCell(..., colspan=2)"],
            ["Styling", "TableStyle(...)", "Per-cell background colors plus banded rows"],
        ],
        caption="Table layout options from simple headers to merged spans.",
        column_widths=[1.2, 2.3, 3.1],
    )
    preview_figure = Figure(
        FIGURE_PATH,
        caption=Paragraph(
            "Example figure loaded directly from the example asset directory."
        ),
        width_inches=3.8,
    )
    grouped_content_box = Box(
        Paragraph(
            "Boxes are meant to be stable grouped containers rather than floating page objects. They render inline in document order."
        ),
        BulletList(
            "Use them for notes, warnings, callouts, or grouped examples.",
            "Regular block objects such as paragraphs, lists, tables, and figures can be nested inside.",
            "Generated pages such as a table of contents or reference list should remain at the document level.",
        ),
        Table(
            headers=["Inside Box", "Status"],
            rows=[
                ["Paragraphs and lists", "supported"],
                ["Tables and figures", "supported"],
            ],
            column_widths=[2.0, 1.4],
        ),
        Figure(FIGURE_PATH, width_inches=1.5),
        title="Grouped Content Example",
        style=BoxStyle(
            border_color="#7A8CA5",
            background_color="#F6F9FC",
            title_background_color="#DDE8F4",
        ),
    )

    return Document(
        "Using docscriptor",
        TableList(),
        FigureList(),
        TableOfContents(),
        Chapter(
            "Getting Started",
            Section(
                "What docscriptor is",
                Paragraph(
                    "Docscriptor is a Python-first document system. You build a document tree with classes such as ",
                    bold("Document"),
                    ", ",
                    bold("Chapter"),
                    ", ",
                    bold("Section"),
                    ", and ",
                    bold("Paragraph"),
                    ", then render the same source into DOCX and PDF.",
                ),
                Paragraph(
                    "This usage guide is intentionally assembled in one ",
                    code("main.py"),
                    " file. New users should be able to read the output document and then read the code beside it without chasing a large helper hierarchy."
                ),
                Paragraph(
                    "The repository itself can be cited directly as ",
                    repository_source.cite(),
                    ", or linked directly as ",
                    link("https://github.com/Gonie-Gonie/pydocs", "GitHub repository"),
                    ". That makes it easy to keep project metadata in the same Python source as the manuscript or report."
                ),
                rendering_outputs_table,
            ),
            Section(
                "Quick Start",
                Paragraph(
                    "The smallest useful workflow is: import the classes you need, compose a document tree, and call ",
                    code("save_docx(...)"),
                    " and ",
                    code("save_pdf(...)"),
                    ".",
                ),
                NumberedList(
                    "Create a Document and give it a title.",
                    "Add Chapter and Section objects to define structure.",
                    "Write prose with Paragraph and inline Text methods.",
                    "Render the same source into DOCX and PDF.",
                ),
                CodeBlock(QUICK_START_SNIPPET, language="python"),
            ),
            Section(
                "How to read this file",
                Paragraph(
                    "Most real projects start simple. Keep one script, one asset directory, and a small number of data files until repetition becomes obvious. Add extra modules later only when there is enough repeated logic to justify them."
                ),
                Paragraph(
                    "That is the reason this guide keeps the object definitions close to the final ",
                    code("Document(...)"),
                    " call. The code is meant to teach the model as much as the rendered document teaches the API."
                ),
            ),
        ),
        Chapter(
            "Document Model",
            Section(
                "Structural objects",
                Paragraph(
                    "A good rule of thumb is: use classes to create things and use methods to perform inline actions. Structural nodes such as ",
                    code("Document"),
                    ", ",
                    code("Chapter"),
                    ", ",
                    code("Section"),
                    ", ",
                    code("Table"),
                    ", and ",
                    code("Figure"),
                    " are instantiated as objects."
                ),
                Paragraph(
                    "This keeps the source readable. When you skim the file, the tree of Python objects closely resembles the tree of headings and blocks in the final document."
                ),
                core_objects_table,
            ),
            Section(
                "Inline actions",
                Paragraph(
                    "Inline formatting remains explicit. You can write ",
                    code("bold(...)"),
                    ", ",
                    code("italic(...)"),
                    ", ",
                    code("code(...)"),
                    ", or ",
                    code("Text.from_markup(...)"),
                    " directly where the text appears."
                ),
                Paragraph(
                    "This sentence mixes ",
                    Text.from_markup("**bold** text, *italic* text, and `code` fragments"),
                    ", plus ",
                    color("colored accents", "#0066AA"),
                    ", without changing how the surrounding document is assembled.",
                ),
                Paragraph(
                    "Portable comments such as ",
                    Comment.annotated(
                        "review notes",
                        "Comments are collected on a generated comments page.",
                    ),
                    ", footnotes such as ",
                    Footnote.annotated(
                        "portable markers",
                        "Portable footnotes stay stable in DOCX and PDF, including inside table cells.",
                    ),
                    ", and inline math such as ",
                    Math.inline(r"\alpha^2 + \beta^2 = \gamma^2"),
                    " can all be authored directly in plain Python.",
                ),
                Equation(r"\int_0^1 \alpha x^2 \, dx = \frac{\alpha}{3}"),
            ),
            Section(
                "Generated pages",
                Paragraph(
                    "Generated pages are regular block objects. Add ",
                    code("TableOfContents()"),
                    ", ",
                    code("TableList()"),
                    ", ",
                    code("FigureList()"),
                    ", ",
                    code("FootnotesPage()"),
                    ", ",
                    code("CommentsPage()"),
                    ", or ",
                    code("ReferencesPage()"),
                    " where you want them to appear in the document."
                ),
                Paragraph(
                    "Because they are just blocks, the document remains predictable: authored content stays in order, while generated summaries are inserted exactly where you place them."
                ),
                generated_pages_table,
            ),
        ),
        Chapter(
            "Layout and Styling",
            Section(
                "Paragraph alignment and spacing",
                Paragraph(
                    "Body paragraphs are justified by default. That gives reports and papers a conventional dense layout without requiring extra style configuration."
                ),
                Paragraph(
                    "If a specific paragraph should be left-aligned, centered, or right-aligned, override it with ",
                    code("ParagraphStyle(alignment=...)"),
                    ". Spacing can be tuned in the same place with ",
                    code("space_after"),
                    " and ",
                    code("leading"),
                    "."
                ),
                Paragraph(
                    "This paragraph is intentionally left-aligned to show a local override.",
                    style=ParagraphStyle(alignment="left", space_after=14),
                ),
            ),
            Section(
                "Heading and list numbering",
                Paragraph(
                    "Headings use ",
                    bold("1"),
                    ", ",
                    bold("1.1"),
                    ", and ",
                    bold("1.1.1"),
                    " by default. Ordered lists use ordinary decimal markers such as ",
                    bold("1."),
                    " and ",
                    bold("2."),
                    "."
                ),
                Paragraph(
                    "Both behaviors can be customized. You can change heading counters with ",
                    code("HeadingNumbering(...)"),
                    ", list markers with ",
                    code("ListStyle(...)"),
                    ", and turn numbering off for article-style front matter with ",
                    code("Section(..., numbered=False)"),
                    "."
                ),
                numbering_table,
                CodeBlock(NUMBERING_SNIPPET, language="python"),
                NumberedList(
                    "Default ordered lists work without any extra configuration.",
                    "Per-list customization is available when a section needs a different marker style.",
                    "Theme-level customization keeps numbering consistent across an entire project.",
                    style=ListStyle(
                        marker_format="upper-roman",
                        prefix="(",
                        suffix=")",
                    ),
                ),
            ),
            Section(
                "Boxes and grouped content",
                Paragraph(
                    "A ",
                    code("Box(...)"),
                    " is the closest equivalent to a simple LaTeX-style callout container. The goal is stability rather than page-floating behavior, so boxes stay inline and follow the normal document flow."
                ),
                Paragraph(
                    "That makes them a good place for notes, review checklists, method summaries, or any grouped content that should not jump around between DOCX and PDF outputs."
                ),
                grouped_content_box,
            ),
        ),
        Chapter(
            "Tables and Figures",
            Section(
                "Tables",
                Paragraph(
                    "Tables can be created directly from headers and rows, or built from dataframe-like objects with ",
                    code("Table.from_dataframe(...)"),
                    ". Table styling lives in ",
                    code("TableStyle(...)"),
                    ", and more precise layouts are available through ",
                    code("TableCell(...)"),
                    " with row and column spans."
                ),
                Paragraph(
                    "The journal paper example in ",
                    code("examples/journal_paper_example/main.py"),
                    " shows the dataframe route in a more realistic workflow. For this guide, the example stays focused on readability and keeps the tables defined inline."
                ),
                table_layout_table,
                CodeBlock(DATA_INTEGRATION_SNIPPET, language="python"),
            ),
            Section(
                "Figures",
                Paragraph(
                    "Figures can come from a stored image file or from any Python object that exposes ",
                    code("savefig()"),
                    ". That makes it easy to insert both pre-made assets and live matplotlib figures."
                ),
                Paragraph(
                    "The figure below is loaded from the local asset directory. In prose, you can refer to the same figure object directly, which renders as ",
                    preview_figure,
                    " once the caption number is known."
                ),
                preview_figure,
            ),
            Section(
                "Referencing captions from prose",
                Paragraph(
                    "Caption references stay stable because they are based on object identity, not on a copied number typed by hand. Reuse the same table or figure object in prose, then place the object later in the document."
                ),
                Paragraph(
                    "For example, ",
                    rendering_outputs_table,
                    " introduces the output strategy for the project, while ",
                    preview_figure,
                    " shows a concrete asset loaded from disk. If the order changes later, the references update with the captions."
                ),
            ),
        ),
        Chapter(
            "Notes and References",
            Section(
                "Footnotes and comments",
                Paragraph(
                    "Docscriptor uses portable footnotes rather than fragile page-bottom placement. Markers appear inline where the note is referenced, and a generated footnotes page collects the full text."
                ),
                Paragraph(
                    "That approach is especially useful when the same content needs to render to both DOCX and PDF. It avoids the layout edge cases that often appear around tables, figures, and page breaks."
                ),
                Paragraph(
                    "Comments work similarly. Use ",
                    code("Comment.annotated(...)"),
                    " for reviewer-style annotations and add ",
                    code("CommentsPage()"),
                    " near the end of the document to collect them."
                ),
            ),
            Section(
                "Citations",
                Paragraph(
                    "Citations can come from direct ",
                    code("CitationSource(...)"),
                    " instances or from a small ",
                    code("CitationLibrary"),
                    ". The direct source route works well for a repository or dataset citation, while a library becomes useful once you have several references to manage."
                ),
                Paragraph(
                    "This guide cites the repository directly as ",
                    repository_source.cite(),
                    " and cites related work from a BibTeX-backed library as ",
                    related_work.cite("knuth1984literate"),
                    ". Only cited sources are included on the generated references page."
                ),
            ),
        ),
        Chapter(
            "Project Layout",
            Section(
                "A simple directory shape",
                Paragraph(
                    "Keep the project layout ordinary. A single script, an asset directory, and a data directory are usually enough until repeated patterns become obvious."
                ),
                Paragraph(
                    "The goal is not to hide document assembly behind a large framework. Most users are better served by a small script they can read from top to bottom."
                ),
                CodeBlock(PROJECT_LAYOUT_SNIPPET, language="text"),
            ),
            Section(
                "Practical workflow",
                Paragraph(
                    "A good working pattern is: keep external assets under version control, generate tables and figures from Python when the source data is already in code, and leave static diagrams as regular files in ",
                    code("assets/"),
                    "."
                ),
                BulletList(
                    "Start with one document script until repetition is clear.",
                    "Keep assets beside the script instead of embedding them in temporary output folders.",
                    "Move repeated data preparation into helper functions before you move presentational code into helper classes.",
                    "Use tests to render representative documents so regressions are caught early.",
                ),
            ),
        ),
        Chapter(
            "End-to-End Workflow",
            Section(
                "Typical sequence",
                NumberedList(
                    "Define sources, assets, tables, and figures as ordinary Python variables.",
                    "Build the document tree with Chapter, Section, Paragraph, and other block objects.",
                    "Insert generated pages where they should appear.",
                    "Call save_docx(...) and save_pdf(...).",
                    "Review the rendered outputs and keep the script under version control.",
                ),
                Paragraph(
                    "The same pattern scales from a short internal report to a structured journal manuscript. The main difference is usually the amount of source data and the number of reusable objects, not a change in the authoring model."
                ),
            ),
            Section(
                "Rule of thumb",
                Paragraph(
                    "If the document is mostly prose, keep the code direct and obvious. If the document is driven by experiment outputs, keep the data loading and plotting logic close enough that the rendered tables and figures can still be traced back to their source."
                ),
                Paragraph(
                    "That balance is the practical center of docscriptor: enough Python to stay synchronized with real project data, but not so much abstraction that a moderately experienced Python user can no longer understand the document source."
                ),
            ),
        ),
        FootnotesPage(),
        CommentsPage(),
        ReferencesPage(),
        author="docscriptor examples",
        summary="Detailed usage guide document",
        subtitle="Detailed usage guide and API walkthrough",
        authors=["docscriptor examples"],
        affiliations=[
            italic("Python-first document authoring toolkit"),
        ],
        cover_page=True,
        theme=Theme(
            show_page_numbers=True,
            page_number_format="{page}",
            heading_numbering=HeadingNumbering(),
        ),
        citations=related_work,
    )


def build_usage_guide(output_dir: str | Path) -> tuple[Path, Path]:
    """Build the usage guide and export it to DOCX and PDF."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document = build_usage_guide_document()
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
