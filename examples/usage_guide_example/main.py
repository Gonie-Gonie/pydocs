"""Standalone usage guide example for docscriptor.

The guide is written as a chapter-based reference document. Each chapter focuses on a
specific authoring concern so a reader can jump directly to the page that matches the
question they have in mind without the document feeling like a FAQ sheet.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from docscriptor import (
    Affiliation,
    Author,
    AuthorLayout,
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
    DocumentSettings,
    Figure,
    FigureList,
    Footnote,
    ImageBox,
    NumberedList,
    PageMargins,
    PageSize,
    Paragraph,
    ReferencesPage,
    Section,
    Shape,
    Sheet,
    Subsection,
    Subsubsection,
    Table,
    TableList,
    TableOfContents,
    Text,
    TextBox,
    Theme,
    TocLevelStyle,
    bold,
    code,
    color,
    link,
)


OUTPUT_DIR = Path("artifacts") / "usage-guide"
EXAMPLE_DIR = Path(__file__).resolve().parent
ASSET_DIR = EXAMPLE_DIR / "assets"
LOGO_PATH = ASSET_DIR / "docscriptor-logo.png"

RELATED_WORK = CitationLibrary(
    [
        CitationSource(
            "Literate Programming",
            key="literate-programming",
            authors=("Donald E. Knuth",),
            publisher="The Computer Journal",
            year="1984",
            url="https://doi.org/10.1093/comjnl/27.2.97",
        ),
        CitationSource(
            "docscriptor repository",
            key="repository",
            organization="Gonie-Gonie",
            publisher="GitHub repository",
            year="2026",
            url="https://github.com/Gonie-Gonie/docscriptor",
        ),
    ]
)

QUICK_START_SNIPPET = """from docscriptor import Chapter, Document, DocumentSettings, Paragraph, Section, bold

report = Document(
    "Hello docscriptor",
    Chapter(
        "Getting Started",
        Section(
            "Overview",
            Paragraph("This document was defined with ", bold("Python objects"), "."),
        ),
    ),
    settings=DocumentSettings(author="Docscriptor"),
)

report.save_docx("artifacts/hello.docx")
report.save_pdf("artifacts/hello.pdf")
report.save_html("artifacts/hello.html")
"""

AUTHOR_LAYOUT_SNIPPET = """from docscriptor import Affiliation, Author, AuthorLayout, DocumentSettings

settings = DocumentSettings(
    authors=[
        Author(
            "Research Lead",
            affiliations=[Affiliation(organization="Example Lab")],
            corresponding=True,
            email="lead@example.org",
        ),
        Author(
            "Implementation Partner",
            affiliations=[Affiliation(organization="Open Source Team")],
            note="GitHub: @example",
        ),
    ],
    author_layout=AuthorLayout(mode="stacked"),
)
"""

LAYOUT_CONTROL_SNIPPET = """from docscriptor import DocumentSettings, PageMargins, PageSize, Theme

settings = DocumentSettings(
    unit="cm",
    page_size=PageSize.a4(),
    page_margins=PageMargins.symmetric(vertical=2.0, horizontal=2.4, unit="cm"),
    theme=Theme(
        footnote_placement="document",
        generated_page_breaks=True,
        table_caption_position="above",
        figure_caption_position="below",
    ),
)
"""

FIGURE_SIZING_SNIPPET = """from docscriptor import DocumentSettings, Figure, PageMargins

settings = DocumentSettings(unit="cm", page_margins=PageMargins.all(2.0, unit="cm"))

figure = Figure(
    "assets/system-diagram.png",
    width=settings.get_text_width(0.75),
    height=8.0,
)
"""

SHEET_SNIPPET = """from docscriptor import ImageBox, Shape, Sheet, TextBox

certificate = Sheet(
    Shape.rect(x=0.4, y=0.4, width=20.2, height=13.2, stroke_color="#D4B56A", stroke_width=1.4),
    ImageBox("assets/docscriptor-logo.png", x=8.7, y=4.0, width=3.6, height=1.6),
    TextBox("Docscriptor Contributor Certificate", x=1.2, y=2.4, width=18.6, height=1.2, align="center", font_size=20),
    TextBox("Awarded for keeping document structure readable across DOCX, PDF, and HTML.", x=2.0, y=6.2, width=17.0, height=1.0, align="center", valign="middle"),
    width=21.0,
    height=14.0,
    unit="cm",
    background_color="#FDFBF6",
)
"""

CONTENTS_CONTROL_SNIPPET = """from docscriptor import TableOfContents, TocLevelStyle

contents = TableOfContents(
    show_page_numbers=True,
    leader=".",
    max_level=3,
    level_styles={
        1: TocLevelStyle(bold=True, space_before=12, space_after=7),
        2: TocLevelStyle(bold=False, space_before=3, space_after=3),
        3: TocLevelStyle(indent=0.48, font_size_delta=-0.2),
    },
)
"""

PROJECT_LAYOUT_SNIPPET = """my-report/
  main.py
  assets/
    logo.png
    architecture.png
  data/
    benchmark.csv
    ablation.csv
  artifacts/
    report.docx
    report.pdf
    report.html
"""


def _wrapped_lines(lines: list[str], *, width: int) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(fill(line, width=width).splitlines())
    return wrapped


def _add_card(
    axis: object,
    x: float,
    y: float,
    width: float,
    height: float,
    color_value: str,
    title: str,
    body: list[str],
    *,
    wrap_width: int = 22,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.2,
        edgecolor="#4F6274",
        facecolor=color_value,
    )
    axis.add_patch(patch)
    axis.text(
        x + width / 2,
        y + height - 0.07,
        title,
        ha="center",
        va="top",
        fontsize=10.5,
        weight="bold",
        color="#173042",
        clip_on=True,
    )
    wrapped = _wrapped_lines(body, width=wrap_width)
    top = y + height - 0.16
    bottom = y + 0.07
    step = min(0.065, max((top - bottom) / max(len(wrapped), 1), 0.04))
    for index, line in enumerate(wrapped):
        axis.text(
            x + 0.03,
            top - (index * step),
            line,
            ha="left",
            va="top",
            fontsize=8.6,
            color="#223847",
            clip_on=True,
        )


def build_pipeline_figure():
    """Create a process diagram that explains the module's core value."""

    figure, axis = plt.subplots(figsize=(8.2, 4.0))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    _add_card(
        axis,
        0.04,
        0.23,
        0.205,
        0.58,
        "#EAF3FB",
        "Project Inputs",
        [
            "CSV / DataFrame results",
            "Static figures and logos",
            "Citations and metadata",
        ],
    )
    _add_card(
        axis,
        0.29,
        0.18,
        0.215,
        0.7,
        "#F8F2E9",
        "Python Document Tree",
        [
            "Document / Chapter / Section",
            "Paragraph, Table, Figure",
            "Explicit comments and footnotes",
        ],
    )
    _add_card(
        axis,
        0.54,
        0.23,
        0.19,
        0.58,
        "#EDF6EC",
        "Indexed Semantics",
        [
            "Heading numbers",
            "Caption references",
            "Generated pages",
        ],
    )
    _add_card(
        axis,
        0.77,
        0.23,
        0.17,
        0.58,
        "#FCEEE8",
        "Rendered Outputs",
        [
            "DOCX for review",
            "PDF for stable export",
            "HTML for quick sharing",
        ],
    )

    arrow_kwargs = {"arrowstyle": "->", "lw": 2.0, "color": "#48627A"}
    axis.annotate("", xy=(0.29, 0.5), xytext=(0.24, 0.5), arrowprops=arrow_kwargs)
    axis.annotate("", xy=(0.54, 0.5), xytext=(0.49, 0.5), arrowprops=arrow_kwargs)
    axis.annotate("", xy=(0.77, 0.5), xytext=(0.72, 0.5), arrowprops=arrow_kwargs)
    axis.text(0.5, 0.93, "One authored structure keeps evidence, layout intent, and exports aligned.", ha="center", fontsize=11, color="#193040")
    figure.tight_layout()
    return figure


def build_author_layout_figure():
    """Create a comparison figure for author-display strategies."""

    figure, axis = plt.subplots(figsize=(8.2, 3.9))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    _add_card(
        axis,
        0.04,
        0.18,
        0.27,
        0.68,
        "#EEF4FB",
        "Journal Default",
        [
            "Name line stays compact",
            "Affiliations are grouped once",
            "Correspondence stays visible",
        ],
        wrap_width=21,
    )
    axis.text(0.175, 0.36, "Hyeong-Gon Jo [1]*", ha="center", fontsize=9.2, color="#173042")
    axis.text(0.175, 0.29, "Codex [2]", ha="center", fontsize=9.2, color="#173042")
    axis.text(0.175, 0.22, "[1] Seoul National University", ha="center", fontsize=8.5, color="#3E5869")

    _add_card(
        axis,
        0.365,
        0.18,
        0.27,
        0.68,
        "#F8F2E8",
        "Stacked Profiles",
        [
            "Useful for guides and reports",
            "Each author gets a short block",
            "Role and note stay readable",
        ],
        wrap_width=21,
    )
    axis.text(0.50, 0.36, "Docscriptor Contributors", ha="center", fontsize=9.5, color="#173042")
    axis.text(0.50, 0.29, "Open-source documentation workflow", ha="center", fontsize=8.8, color="#3E5869")
    axis.text(0.50, 0.22, "Maintainers and release editors", ha="center", fontsize=8.8, color="#3E5869")

    _add_card(
        axis,
        0.69,
        0.18,
        0.27,
        0.68,
        "#EDF7EC",
        "Manual Front Matter",
        [
            "When the cover needs a custom layout",
            "Keep metadata simple",
            "Author full title blocks in content",
        ],
        wrap_width=21,
    )
    axis.text(0.825, 0.36, "DocumentSettings(", ha="center", fontsize=9.0, color="#173042")
    axis.text(0.825, 0.30, "author='Team Name')", ha="center", fontsize=9.0, color="#173042")
    axis.text(0.825, 0.22, "Use unnumbered sections for the visual cover.", ha="center", fontsize=8.4, color="#3E5869")

    figure.tight_layout()
    return figure


def build_renderer_behavior_figure():
    """Create a renderer comparison figure for notes and references."""

    figure, axis = plt.subplots(figsize=(8.2, 3.5))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    columns = [
        ("DOCX", "#EAF3FB", ["Native review editing", "Page footnotes by default", "Stable cross-references"]),
        ("PDF", "#F8F2E8", ["Stable final layout", "Generated notes fallback", "Caption and figure cohesion"]),
        ("HTML", "#EDF7EC", ["Fast browser sharing", "Generated notes fallback", "Anchor-friendly navigation"]),
    ]
    for index, (title, color_value, lines) in enumerate(columns):
        x = 0.05 + (index * 0.31)
        _add_card(axis, x, 0.18, 0.26, 0.68, color_value, title, lines, wrap_width=20)

    axis.text(0.5, 0.88, "Renderer behavior is shared where possible and explicit where it differs.", ha="center", fontsize=10.5, color="#1A3345")
    figure.tight_layout()
    return figure


def build_usage_guide_document() -> Document:
    """Build a detailed reference-style usage guide."""

    logo_figure = Figure(LOGO_PATH, width=1.8)
    pipeline_figure = Figure(
        build_pipeline_figure(),
        caption=Paragraph(
            "Core authoring pipeline from project inputs to synchronized DOCX, PDF, and HTML outputs."
        ),
        width=6.5,
    )
    author_layout_figure = Figure(
        build_author_layout_figure(),
        caption=Paragraph(
            "Three practical author-display strategies: journal-style default, stacked guide profiles, and fully manual front matter."
        ),
        width=6.5,
    )
    renderer_behavior_figure = Figure(
        build_renderer_behavior_figure(),
        caption=Paragraph(
            "Renderer-specific behavior for notes, review workflows, and cross-reference stability."
        ),
        width=6.5,
    )

    navigation_table = Table(
        headers=["Need", "Recommended chapter", "What you will find there"],
        rows=[
            ["First successful export", "1. Overview", "The minimal document shape, the save methods, and the default rendering model."],
            ["Author metadata and covers", "2. Metadata and Title Matter", "Structured authors, journal-style defaults, stacked profiles, and cover conventions."],
            ["Tables, figures, and references", "4. Tables, Figures, and Cross-References", "Caption numbering, block references, and data-backed media objects."],
            ["Notes and citations", "5. Notes, Comments, and References", "Footnotes, generated comments pages, citation libraries, and bibliography output."],
            ["Pagination and output differences", "6. Layout and Pagination", "Contents styling, caption cohesion, and renderer-specific note behavior."],
        ],
        caption="A reading map for the guide.",
        column_widths=[2.0, 2.0, 2.6],
    )
    author_options_table = Table(
        headers=["Approach", "When it fits best", "Configuration pattern"],
        rows=[
            ["Structured journal default", "Manuscripts and technical reports with compact title matter.", "DocumentSettings(authors=[...])"],
            ["Structured stacked profiles", "Guides, internal reports, and project documentation.", "DocumentSettings(authors=[...], author_layout=AuthorLayout(mode='stacked'))"],
            ["Simple metadata string", "Short exports where file properties matter more than visible title blocks.", "DocumentSettings(author='Team Name')"],
            ["Manual front matter section", "Branded covers or institution-specific title pages.", "Keep metadata simple and author the visible cover with unnumbered sections."],
        ],
        caption="Author-display options from most automated to most manual.",
        column_widths=[1.8, 2.5, 2.3],
    )
    generated_pages_table = Table(
        headers=["Generated object", "Why it exists", "What triggers it"],
        rows=[
            ["TableOfContents()", "Creates a navigable outline from authored headings.", "Place the block where the contents page should appear."],
            ["TableList() / FigureList()", "Collects numbered captions in a stable order.", "Use captioned tables or figures earlier in the document."],
            ["CommentsPage()", "Exports reviewer comments without disturbing reading flow.", Comment.annotated("Place review remarks inline", "CommentsPage() collects these review notes onto a dedicated generated page.")],
            ["ReferencesPage()", "Renders only the bibliography entries that were cited.", "Cite items from CitationLibrary or CitationSource."],
        ],
        caption="Generated pages that help a long document stay navigable.",
        column_widths=[1.8, 2.3, 2.5],
    )
    media_workflow_table = Table(
        headers=["Task", "Preferred object", "Why the object matters"],
        rows=[
            ["Insert a benchmark table from code", "Table.from_dataframe(...)", "The rendered table stays attached to the data-processing step that created it."],
            ["Insert an architecture figure from disk", "Figure('assets/diagram.png')", "Static diagrams can stay under version control without manual copy-paste."],
            ["Refer to a caption from prose", "Paragraph('See ', figure_obj, '.')", "Block references update automatically when figure order changes."],
            ["Keep a note near evidence", Footnote.annotated("page-footnote default", "DOCX uses page footnotes by default. PDF and HTML keep a generated notes page because their layout engines do not share Word's native footnote model."), "Footnotes stay authored inline instead of being managed in a separate editor pane."],
        ],
        caption="Working patterns for media objects and references.",
        column_widths=[1.9, 2.0, 2.7],
    )
    renderer_rules_table = Table(
        headers=["Concern", "Shared behavior", "Important renderer detail"],
        rows=[
            ["Heading numbering", "Document structure drives numbering in all outputs.", "The contents page reflects the authored hierarchy rather than a separate outline tool."],
            ["Captions", "Tables and figures receive automatic numbers and can be referenced inline.", "Captions are kept visually closer to their table or figure to avoid page-break confusion."],
            ["Footnotes", "Footnotes are authored with the same inline API everywhere.", "DOCX uses native page footnotes; PDF and HTML fall back to generated note pages."],
            ["Hyperlinks", "External links and block anchors remain visible in all outputs.", "HTML makes them directly clickable while DOCX and PDF preserve them in exported files."],
        ],
        caption="Behavior that stays stable across renderers and the places where format details still matter.",
        column_widths=[1.5, 2.7, 2.4],
    )
    page_layout_table = Table(
        headers=["Need", "API", "Effect"],
        rows=[
            ["Work in metric units", "DocumentSettings(unit='cm')", "Numeric lengths are interpreted as centimeters unless an object overrides unit."],
            ["Set paper size", "PageSize.a4(), PageSize.letter(), or PageSize(width, height, unit=...)", "DOCX, PDF, and HTML use the same page box."],
            ["Set printable margins", "PageMargins.all(...) or PageMargins.symmetric(...)", "The text area and HTML @page margins stay aligned."],
            ["Force a new page", "PageBreak()", "The break is explicit in the document tree and renders across DOCX, PDF, and HTML."],
            ["Size a figure from text width", "settings.get_text_width(0.75)", "Figures can follow the document text block instead of hard-coded page assumptions."],
        ],
        caption="Page layout controls shared across renderers.",
        column_widths=[1.7, 2.6, 2.6],
    )
    contents_style_table = Table(
        headers=["Concern", "Default", "Customization path"],
        rows=[
            ["Page numbers", "Shown by default with right-aligned page labels.", "Set TableOfContents(show_page_numbers=False) to hide them."],
            ["Leader dots", "Dotted leaders connect the heading text to the page number.", "Set leader='' for no leader or another short string for a different visual cue."],
            ["Heading depth", "All numbered headings are included.", "Set max_level=2 or max_level=3 for shorter contents pages."],
            ["Hierarchy styling", "Top-level entries are bold; lower levels use normal weight by default.", "Pass level_styles={level: TocLevelStyle(...)} for per-level spacing, indentation, and emphasis."],
        ],
        caption="Table-of-contents defaults and customization options.",
        column_widths=[1.6, 2.7, 2.7],
    )
    figure_sizing_table = Table(
        headers=["Figure intent", "Pattern", "Renderer behavior"],
        rows=[
            ["Constrain by width", "Figure(path, width=12, unit='cm')", "The image keeps its aspect ratio while fitting the requested width."],
            ["Constrain by height", "Figure(path, height=8, unit='cm')", "The image keeps its aspect ratio while fitting the requested height."],
            ["Force a box", "Figure(path, width=12, height=8, unit='cm')", "Both dimensions are honored, similar to explicit LaTeX graphic sizing."],
            ["Follow text width", "Figure(path, width=settings.get_text_width(0.8))", "The width is computed from page size minus margins."],
        ],
        caption="Figure sizing patterns for width, height, and document-relative sizing.",
        column_widths=[1.8, 2.9, 2.3],
    )
    scaling_table = Table(
        headers=["Project stage", "Suggested structure", "Reasoning"],
        rows=[
            ["Single script", "Keep document assembly in one main.py file.", "The document tree stays visible while the project is still changing rapidly."],
            ["Growing assets", "Split reusable chart builders or citation helpers into local modules.", "Move code only when repeated logic starts to hide the document structure."],
            ["Team workflow", "Keep data, assets, and document outputs in sibling folders.", "It becomes easier to review analysis changes and document changes together."],
            ["Release workflow", "Render artifacts in CI and attach them to GitHub releases.", "The exported files and the package version can move together."],
        ],
        caption="How the source layout can grow without losing readability.",
        column_widths=[1.4, 2.3, 2.9],
    )

    cover_callout = Box(
        Paragraph(
            "This guide stays intentionally close to the authored source. The point is not only to document the API, but also to let a new user read the script and see how the Python tree maps to the final pages."
        ),
        BulletList(
            "Keep title matter, metadata, and theme choices near DocumentSettings(...).",
            "Keep block structure explicit so chapters and sections remain visible in code review.",
            "Treat figures, tables, and notes as authored objects rather than pasted export artifacts.",
        ),
        title="Reading Principle",
        style=BoxStyle(
            border_color="#6E8497",
            background_color="#F6F9FC",
            title_background_color="#DCE8F4",
        ),
    )
    contributor_certificate = Sheet(
        Shape.rect(
            x=0.4,
            y=0.4,
            width=20.2,
            height=13.2,
            stroke_color="#D4B56A",
            stroke_width=1.4,
        ),
        Shape.rect(
            x=0.8,
            y=0.8,
            width=19.4,
            height=12.4,
            stroke_color="#6E8497",
            stroke_width=0.8,
        ),
        Shape.ellipse(
            x=9.0,
            y=10.8,
            width=3.0,
            height=1.2,
            stroke_color="#B2783D",
            fill_color="#FFF1D8",
        ),
        ImageBox(
            LOGO_PATH,
            x=8.7,
            y=4.0,
            width=3.6,
            height=1.6,
            z_index=1,
        ),
        TextBox(
            "Docscriptor Contributor Certificate",
            x=1.2,
            y=2.4,
            width=18.6,
            height=1.2,
            align="center",
            font_size=20,
            z_index=2,
        ),
        TextBox(
            "Awarded for keeping document structure readable across DOCX, PDF, and HTML.",
            x=2.0,
            y=6.2,
            width=17.0,
            height=1.0,
            align="center",
            valign="middle",
            font_size=11,
            z_index=2,
        ),
        TextBox(
            "Generated from the same Python document tree as this guide.",
            x=3.0,
            y=8.2,
            width=15.0,
            height=0.8,
            align="center",
            font_size=10,
            z_index=2,
        ),
        TextBox(
            "docscriptor",
            x=8.0,
            y=11.1,
            width=5.0,
            height=0.6,
            align="center",
            font_size=12,
            z_index=2,
        ),
        width=21.0,
        height=14.0,
        unit="cm",
        background_color="#FDFBF6",
        border_color="#D4B56A",
        border_width=0.8,
    )

    return Document(
        "Docscriptor User Guide",
        Section(
            "Guide Cover",
            logo_figure,
            Paragraph(
                bold("License. "),
                "MIT. The package metadata, source code, and example release workflow all live in the same repository so the rendered outputs can be attached to a tagged release."
            ),
            Paragraph(
                bold("Repository. "),
                link("https://github.com/Gonie-Gonie/docscriptor", "github.com/Gonie-Gonie/docscriptor"),
                ".",
            ),
            Paragraph(
                bold("Positioning. "),
                "Docscriptor is for situations where document content already lives near Python data, figures, scripts, and review workflows."
            ),
            cover_callout,
            level=2,
            numbered=False,
        ),
        TableOfContents(),
        TableList(),
        FigureList(),
        Chapter(
            "Overview",
            Section(
                "What docscriptor is trying to solve",
                Paragraph(
                    "Docscriptor is a Python-first document authoring toolkit. It lets you define a document with ordinary Python objects, render the same source to DOCX, PDF, and HTML, and keep data-backed tables and figures close to the code that generated them."
                ),
                Paragraph(
                    "The central motivation is the one described in ",
                    RELATED_WORK.cite("literate-programming"),
                    ": authorship becomes easier to trust when prose, evidence, and automation live in one readable source."
                ),
                pipeline_figure,
                Paragraph(
                    "The pipeline shown in ",
                    pipeline_figure,
                    " is the real payoff of the package. Data files, static assets, title metadata, generated pages, and renderer output all remain downstream of one explicit document tree."
                ),
                navigation_table,
            ),
            Section(
                "The smallest working document",
                Paragraph(
                    "A first document only needs a title, a chapter, a section, a paragraph, and one save call per output format. The quick-start example below intentionally uses ",
                    code("bold(...)"),
                    " rather than older method-style emphasis so the current preferred inline API stays visible."
                ),
                CodeBlock(QUICK_START_SNIPPET, language="python"),
                NumberedList(
                    "Author the structure with Document, Chapter, and Section objects.",
                    "Write prose with Paragraph plus explicit inline helpers such as bold(...), code(...), and links.",
                    "Render to DOCX when collaboration requires editing, PDF when layout stability matters, and HTML when lightweight sharing is enough.",
                ),
            ),
        ),
        Chapter(
            "Metadata and Title Matter",
            Section(
                "Structured authors as the default path",
                Paragraph(
                    "The default structured-author path is now journal-friendly without forcing every document to look like a journal submission. If you provide ",
                    code("Author(...)"),
                    " objects, docscriptor groups names, affiliations, and correspondence information into a compact title block by default."
                ),
                Paragraph(
                    "That default fits papers well, but guides often read better with stacked author profiles. This guide therefore uses ",
                    code("AuthorLayout(mode='stacked')"),
                    " while the journal example relies on the default journal-style arrangement."
                ),
                author_layout_figure,
                author_options_table,
            ),
            Section(
                "When to customize the author display",
                Paragraph(
                    "The practical decision is simple: use the journal default when the visible priority is compact authorship, use stacked profiles when the document benefits from role context, and fall back to a simple metadata author string when visible title matter is mostly manual."
                ),
                CodeBlock(AUTHOR_LAYOUT_SNIPPET, language="python"),
                Paragraph(
                    "If even the stacked layout is still too opinionated, keep ",
                    code("DocumentSettings(author='Team Name')"),
                    " for metadata and author the visible cover with ordinary unnumbered sections instead. That preserves a clean file property string while leaving the page design fully under document control."
                ),
            ),
        ),
        Chapter(
            "Document Model",
            Section(
                "Blocks define the visible structure",
                Paragraph(
                    "A good rule is: use classes for visible structure and helpers for inline emphasis. Blocks such as ",
                    code("Chapter"),
                    ", ",
                    code("Section"),
                    ", ",
                    code("Table"),
                    ", and ",
                    code("Figure"),
                    " make the document outline obvious when reading the source."
                ),
                Paragraph(
                    "That explicitness matters most in large edits. During review, a collaborator can skim the object tree and understand where a figure belongs or where a generated page is inserted without first running the script."
                ),
                generated_pages_table,
            ),
            Section(
                "Inline annotations stay local to the prose",
                Paragraph(
                    "Inline helpers are deliberately direct. Use ",
                    code("bold(...)"),
                    ", ",
                    code("code(...)"),
                    ", hyperlinks, comments such as ",
                    Comment.annotated("reviewable phrases", "This note will show up again on the generated comments page."),
                    ", and notes such as ",
                    Footnote.annotated(
                        "portable footnotes",
                        "Portable footnotes are authored inline so the prose remains readable in Python. The visible placement depends on renderer capabilities.",
                    ),
                    " exactly where the text appears."
                ),
                Paragraph(
                    "That local authorship pattern is also why the guide can stay detailed without becoming confusing. The content reads like a normal reference document, but the source remains inspectable because the formatting instructions are still attached to the words they affect."
                ),
            ),
        ),
        Chapter(
            "Tables, Figures, and Cross-References",
            Section(
                "Media objects should stay attached to evidence",
                Paragraph(
                    "Tables and figures become much easier to trust when they are declared as document objects instead of exported manually. A captioned block can also be referenced from prose by inserting the block object itself inside a paragraph."
                ),
                media_workflow_table,
                Paragraph(
                    "That block-reference behavior is especially helpful in late revisions. When the order of figures or tables changes, the text stays synchronized because references resolve against the indexed caption numbers rather than a hard-coded label."
                ),
            ),
            Section(
                "Use figures to explain the authoring model, not just decorate it",
                Paragraph(
                    "The diagrams in this guide are intentionally explanatory. ",
                    pipeline_figure,
                    " captures the project-level data flow, while ",
                    author_layout_figure,
                    " explains how the same metadata can support multiple presentation styles."
                ),
                renderer_behavior_figure,
                Paragraph(
                    "Likewise, ",
                    renderer_behavior_figure,
                    " is not decorative. It surfaces the concrete behavior differences a user needs to know before choosing which output to send to collaborators."
                ),
            ),
        ),
        Chapter(
            "Notes, Comments, and References",
            Section(
                "Footnotes and comments",
                Paragraph(
                    "Footnotes are meant for reader-facing context, while comments are for review-facing discussion. The two features are authored in the same inline style but flow to different places in the rendered outputs."
                ),
                Paragraph(
                    "The most important recent behavior change is that page-footnote placement is the default target when the renderer can support it. In practice that means DOCX uses native footnotes, while PDF and HTML fall back to a generated notes page because they do not share Word's native footnote mechanism."
                ),
                Paragraph(
                    "If you want the explicit collected-notes behavior everywhere, set ",
                    code("Theme(footnote_placement='document')"),
                    ".",
                ),
                CodeBlock(LAYOUT_CONTROL_SNIPPET, language="python"),
            ),
            Section(
                "Citations and bibliography output",
                Paragraph(
                    "Citations work the same way as table and figure references: keep them attached to the prose. The repository itself can be cited as ",
                    RELATED_WORK.cite("repository"),
                    ", which is useful when a guide or report needs to point back to the implementation source directly."
                ),
                Paragraph(
                    "Only cited sources are rendered on the final references page. That keeps the bibliography stable even when a project carries a larger citation library than any single document uses."
                ),
            ),
        ),
        Chapter(
            "Layout and Pagination",
            Section(
                "What the theme controls",
                Paragraph(
                    "Theme is where renderer-neutral layout defaults live: heading numbering, list markers, page numbers, caption positions, author alignment, and footnote placement strategy. The goal is to keep document-wide choices together so a document does not accumulate hidden style decisions."
                ),
                renderer_rules_table,
            ),
            Section(
                "Page size, margins, and explicit breaks",
                Paragraph(
                    "Page geometry belongs in ",
                    code("DocumentSettings"),
                    " rather than in individual renderer calls. Use ",
                    code("PageSize"),
                    " for the physical page, ",
                    code("PageMargins"),
                    " for the printable area, and ",
                    code("unit"),
                    " to make numeric dimensions read naturally for the document."
                ),
                page_layout_table,
                Paragraph(
                    "Explicit pagination is a block-level decision. Insert ",
                    code("PageBreak()"),
                    " where the authored flow should move to the next page; generated pages can still use ",
                    code("Theme(generated_page_breaks=True)"),
                    " for automatic separation."
                ),
                CodeBlock(LAYOUT_CONTROL_SNIPPET, language="python"),
            ),
            Section(
                "Contents hierarchy and page labels",
                Paragraph(
                    "The generated contents page uses hierarchy-aware spacing and emphasis by default. It also renders page labels with dotted leaders, which is the common book/report convention where the entry text sits on the left and the page number aligns on the right."
                ),
                Paragraph(
                    "Use ",
                    code("TableOfContents"),
                    " options when the document needs a shorter outline, no page numbers, or a different per-level visual rhythm."
                ),
                contents_style_table,
                CodeBlock(CONTENTS_CONTROL_SNIPPET, language="python"),
                Subsection(
                    "Subsection entries",
                    Paragraph(
                        "This subsection is included as a live example of a third-level heading. It should appear in the contents below the section with normal font weight and a deeper indent."
                    ),
                    Subsubsection(
                        "Subsubsection entries",
                        Paragraph(
                            "This fourth-level heading gives the contents page one more depth to render, which makes hierarchy checks easier in examples and tests."
                        ),
                    ),
                ),
            ),
            Section(
                "Figure sizing from document geometry",
                Paragraph(
                    "Figures accept ",
                    code("width"),
                    ", ",
                    code("height"),
                    ", or both. If only one dimension is set, renderers preserve the image aspect ratio. If both are set, the figure is placed into the explicit box."
                ),
                Paragraph(
                    "For LaTeX-like sizing relative to the text block, compute the length before constructing the figure. The common pattern is ",
                    code("width=settings.get_text_width(0.75)"),
                    ", which reads as '75 percent of the current text width' while still producing a plain numeric width."
                ),
                figure_sizing_table,
                CodeBlock(FIGURE_SIZING_SNIPPET, language="python"),
            ),
            Section(
                "Fixed sheets for short forms",
                Paragraph(
                    "Most docscriptor pages should remain flowing document structure. When a project needs a one-page form such as a certificate, badge, or cover insert, use ",
                    code("Sheet"),
                    " as a normal block inside the same document tree. Its coordinates are measured from the top-left corner, which keeps small form layouts readable without turning the whole document into a slide deck."
                ),
                contributor_certificate,
                CodeBlock(SHEET_SNIPPET, language="python"),
            ),
            Section(
                "What changed in the default document feel",
                Paragraph(
                    "The generated contents page now separates top-level chapters more clearly so readers can distinguish chapters, sections, and deeper levels at a glance. Captions are also kept visually closer to their table or figure so page breaks are less likely to strand a label away from the object it describes."
                ),
                Paragraph(
                    "Those changes matter because docscriptor is not trying to imitate a notebook export. It should read like an intentionally typeset document even when the source stays fully programmable."
                ),
            ),
        ),
        Chapter(
            "Project Structure and Scaling Up",
            Section(
                "When to split a single file",
                Paragraph(
                    "Start with one file and only split when real repetition appears. The object tree is the most valuable teaching tool in a new project, so it should remain visible until helper functions provide a clear readability gain."
                ),
                scaling_table,
            ),
            Section(
                "Repository layout that stays review-friendly",
                Paragraph(
                    "A healthy document repository keeps authored source, reusable assets, structured data, and generated artifacts separate. That keeps commits readable and makes it easier to review whether a table changed because the data changed or because the document layout changed."
                ),
                CodeBlock(PROJECT_LAYOUT_SNIPPET, language="text"),
                Paragraph(
                    "The journal example at ",
                    code("examples/journal_paper_example/main.py"),
                    " follows the same pattern with CSV-backed tables, generated figures, and a manuscript body authored from one readable script."
                ),
            ),
        ),
        CommentsPage(),
        ReferencesPage(),
        settings=DocumentSettings(
            author="Docscriptor Contributors",
            summary="Detailed usage guide and API walkthrough",
            subtitle="Reference-style guide for structured Python document authoring",
            authors=[
                Author(
                    "Docscriptor Contributors",
                    affiliations=["Open-source documentation workflow"],
                    note="Maintainers and release editors",
                ),
                Author(
                    "Hyeong-Gon Jo",
                    affiliations=[
                        Affiliation(
                            department="Building Simulation LAB",
                            organization="Seoul National University",
                            city="Seoul",
                            country="Republic of Korea",
                        )
                    ],
                    note="Repository steward",
                ),
            ],
            author_layout=AuthorLayout(mode="stacked"),
            page_margins=PageMargins.symmetric(vertical=2.0, horizontal=2.2, unit="cm"),
            theme=Theme(
                show_page_numbers=True,
                page_number_format="{page}",
                footnote_placement="page",
            ),
        ),
        citations=RELATED_WORK,
    )


def build_usage_guide(output_dir: str | Path) -> tuple[Path, Path]:
    """Build the usage guide example and export it to DOCX, PDF, and HTML."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document = build_usage_guide_document()
    docx_path = output_path / "docscriptor-user-guide.docx"
    pdf_path = output_path / "docscriptor-user-guide.pdf"
    html_path = output_path / "docscriptor-user-guide.html"
    document.save_docx(docx_path)
    document.save_pdf(pdf_path)
    document.save_html(html_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the guide into the default example output directory."""

    docx_path, pdf_path = build_usage_guide(OUTPUT_DIR)
    html_path = OUTPUT_DIR / "docscriptor-user-guide.html"
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
