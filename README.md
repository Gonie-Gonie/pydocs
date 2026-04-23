# docscriptor

Docscriptor is an early-stage, Python-first alternative to LaTeX for teams who want documents to be defined with regular Python code.
The long-term goal is to compose structured content in scripts, reuse templates and components, and render the same source into PDF and DOCX outputs.

## Vision

- define documents with normal Python modules, functions, and data structures
- make document generation programmable, testable, and reusable
- support multiple export targets without committing to a TeX-centric workflow

## Current Structure

The package now ships with a modular document model plus two renderers:

- `document.py` for the root `Document` entry point
- `blocks.py` for structural and block-level objects such as `Chapter`, `Section`, `Paragraph`, `CodeBlock`, `Box`, and generated pages
- `inline.py` for inline fragments and content-transforming methods such as `Text.bold(...)`, `Text.from_markup(...)`, `Comment.annotated(...)`, and `Footnote.annotated(...)`
- `tables.py` for `Table`, `TableCell`, dataframe support, and `Figure`
- `styles.py` for `TextStyle`, `ParagraphStyle`, `HeadingNumbering`, `ListStyle`, `BoxStyle`, `TableStyle`, and `Theme`
- `references.py` for `CitationSource`, `CitationLibrary`, and bibliography helpers
- `renderers/docx.py` and `renderers/pdf.py` for format-specific layout logic driven by each block's `render_to_docx(...)` and `render_to_pdf(...)` methods

## Authoring Model

The intended workflow is:

1. define a document tree with Python instances
2. subclass the provided building blocks when you want reusable semantics
3. render the same tree into one or more output formats

Instantiate structural nodes directly with classes such as `Document`, `Chapter`, `Section`, and `Paragraph`.
That same rule applies to lists, so use `BulletList` and `NumberedList` directly instead of constructor-style wrapper functions.
For inline actions, prefer explicit methods when they read well, such as `Text.bold(...)`, `Text.from_markup(...)`, `Comment.annotated(...)`, `Footnote.annotated(...)`, `Math.inline(...)`, or `CitationSource.cite()`.
The helper functions remain available as short compatibility aliases for the same transformations.
The default theme uses Times New Roman for body copy and progressively stronger heading treatment for chapter and section levels.
Headings are numbered by default using labels such as `1`, `1.1`, and `1.1.1`, and both heading numbering and list marker styles can be customized with `HeadingNumbering(...)` and `ListStyle(...)`.
Captioned tables and figures are numbered automatically, can be cited from prose by reusing the same object instance, and can be collected into generated lists.
Tables can be authored explicitly with spanned `TableCell(...)` objects or built directly from dataframe-like objects, and figures can be rendered either from filesystem paths or from `savefig()`-compatible Python objects.
Bibliography data can be supplied with Python objects or as a BibTeX string, then rendered through `cite(...)` and a generated references page that only includes cited sources.
Generated front matter such as a table of contents or lists of tables and figures is rendered with section-level headings so it reads like part of the document structure.
Portable footnotes are rendered as inline superscript markers and collected on a generated footnotes page so the behavior stays stable across both DOCX and PDF outputs, including inside table cells.

The core model in `docscriptor.model` is intentionally class-based so users can build their own abstractions on top.
For example, a team can subclass `Paragraph`, `Section`, or `Document` to create house styles, reusable callouts, or report templates.

```python
from docscriptor import Paragraph, ParagraphStyle, Text


class WarningParagraph(Paragraph):
    def __init__(self, *content):
        super().__init__(
            Text.bold("Warning: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )
```

Example:

```python
from docscriptor import (
    Chapter,
    Document,
    CodeBlock,
    Figure,
    FigureList,
    TableList,
    CitationSource,
    Paragraph,
    ReferencesPage,
    Section,
    Subsection,
    Subsubsection,
    Table,
    TableOfContents,
    Text,
)

metrics_table = Table(
    headers=["Metric", "Value"],
    rows=[
        ["Latency", "14 ms"],
        ["Success rate", "99.8%"],
    ],
    caption="Summary metrics.",
)
output_figure = Figure(
    "example.png",
    caption=Paragraph("Example output."),
    width_inches=3.0,
)
repository_source = CitationSource(
    "Experiment assets",
    organization="Docscriptor",
    year="2026",
    url="https://github.com/Gonie-Gonie/pydocs",
)

report = Document(
    "Experiment Report",
    Chapter(
        "Analysis",
        Section(
            "Overview",
            Paragraph(
                "This document was written in Python with ",
                Text.styled("custom emphasis", bold=True),
                " and ",
                Text.from_markup("**lightweight** *markup* support."),
            ),
            Paragraph(
                "See ",
                metrics_table,
                " and ",
                output_figure,
                " for the exported assets. Repository metadata appears in ",
                repository_source.cite(),
                ".",
            ),
            Subsection(
                "Measurements",
                metrics_table,
                Subsubsection(
                    "Exports",
                    CodeBlock(
                        "report.save_docx('artifacts/report.docx')\nreport.save_pdf('artifacts/report.pdf')",
                        language="python",
                    ),
                ),
            ),
            output_figure,
            TableOfContents(),
            Paragraph(Text.bold("Rendered inline labels remain easy to spot.")),
            TableList(),
            FigureList(),
            ReferencesPage(),
        ),
    ),
    author="Docscriptor",
)
```

## Example Script

The repository includes a package-style usage guide example under `examples/usage_guide_example/`.
That example keeps its reusable snippets, citations, tables, and bundled assets in separate files while preserving a simple compatibility entrypoint:

```powershell
python -m examples.usage_guide
```

By default it writes these files under `artifacts/usage-guide/`:

- `docscriptor-usage-guide.docx`
- `docscriptor-usage-guide.pdf`

This example is also covered by automated tests so the generated outputs stay exercised continuously.

## Development

Assuming Python 3.14 is already installed on the machine, run the repository setup helper:

```powershell
.\scripts\setup-repo.cmd
```

If you prefer to run the PowerShell script directly, use a one-off execution policy bypass for the current invocation:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-repo.ps1
```

The script will:

- find Python 3.14
- create or reuse `.venv`
- upgrade `pip`
- install the project in editable mode with `dev` dependencies

To activate the virtual environment manually after setup:

```powershell
.\.venv\Scripts\Activate.ps1
```

## VS Code

This repository commits workspace settings for VS Code.
After running `.\scripts\setup-repo.cmd`, opening the folder in VS Code should pick `.venv` as the default interpreter and enable pytest discovery for the `tests` folder.

Run the test suite:

```powershell
pytest
```

Build distribution artifacts:

```powershell
python -m build
```
