# docscriptor

Docscriptor is a Python-first document authoring toolkit for people who want to define structured documents with normal Python code and render the same source to both DOCX and PDF.

It is aimed at report, documentation, and manuscript workflows where content already lives near Python data, figures, and scripts.

## Install

Install the core package:

```powershell
pip install docscriptor
```

Install the extra dependencies used by the example scripts:

```powershell
pip install "docscriptor[examples]"
```

For local development:

```powershell
pip install -e ".[dev]"
```

## Quick Start

```python
from docscriptor import Chapter, Document, Paragraph, Section, Text

report = Document(
    "Hello docscriptor",
    Chapter(
        "Getting Started",
        Section(
            "Overview",
            Paragraph(
                "This document was defined with ",
                Text.bold("Python objects"),
                ".",
            ),
        ),
    ),
    author="Docscriptor",
)

report.save_docx("artifacts/hello.docx")
report.save_pdf("artifacts/hello.pdf")
```

## Authoring Model

Docscriptor tries to keep the source readable:

- create objects with classes such as `Document`, `Chapter`, `Section`, `Paragraph`, `Table`, and `Figure`
- apply inline actions with methods such as `Text.bold(...)`, `Text.italic(...)`, `Text.code(...)`, `Text.from_markup(...)`, `Comment.annotated(...)`, `Footnote.annotated(...)`, and `CitationSource.cite()`
- keep the document tree explicit so the Python structure matches the final output structure

The default behavior is intentionally conventional:

- paragraphs are justified by default
- headings are numbered as `1`, `1.1`, `1.1.1`, and so on
- ordered and bullet lists can be customized with `ListStyle(...)`
- heading numbering can be customized with `HeadingNumbering(...)`
- article-style front matter can be left unnumbered with `Section(..., numbered=False)`

## Features

- DOCX and PDF rendering from the same document tree
- block objects for paragraphs, lists, code blocks, equations, boxes, tables, figures, and generated pages
- portable comments and footnotes that stay stable across both outputs
- captioned tables and figures with automatic numbering and in-text references
- table support for `TableCell(...)`, `rowspan`, `colspan`, banded rows, and dataframe-like inputs
- figure support for both stored image files and `savefig()`-compatible Python objects
- bibliography support through `CitationSource`, `CitationLibrary`, direct citation objects, and BibTeX import

## Example Scripts

The repository includes two standalone example directories:

- `examples/usage_guide_example/`
- `examples/journal_paper_example/`

Run them directly:

```powershell
python .\examples\usage_guide_example\main.py
python .\examples\journal_paper_example\main.py
```

What they show:

- `usage_guide_example` is a detailed guide that keeps almost all assembly in one `main.py` so the source stays easy to read
- `journal_paper_example` shows a longer manuscript-style workflow with article-style sections, unnumbered abstract/highlights/acknowledgements, CSV-backed tables, and matplotlib figures inserted directly from Python objects

By default they write outputs under:

- `artifacts/usage-guide/`
- `artifacts/journal-paper/`

## Project Layout

The package is organized by responsibility:

- `src/docscriptor/document.py` for the root `Document`
- `src/docscriptor/blocks.py` for structural and block-level objects
- `src/docscriptor/inline.py` for inline fragments and action-style helpers
- `src/docscriptor/tables.py` for tables, table cells, dataframe support, and figures
- `src/docscriptor/styles.py` for paragraph, numbering, table, box, and theme configuration
- `src/docscriptor/references.py` for bibliography objects and BibTeX import
- `src/docscriptor/renderers/docx.py` and `src/docscriptor/renderers/pdf.py` for format-specific layout

## Development

Assuming Python 3.14 is installed:

```powershell
.\scripts\setup-repo.cmd
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-repo.ps1
```

Run tests:

```powershell
pytest
```

Build distribution artifacts:

```powershell
python -m build
```
