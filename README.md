# docscriptor

Docscriptor is a Python-first document authoring toolkit for people who want to define structured documents with normal Python code and render the same source to DOCX, PDF, and HTML.

It is aimed at report, documentation, and manuscript workflows where content already lives near Python data, figures, and scripts.

## Install

Docscriptor is not published on PyPI yet, so `pip install docscriptor` will not work at the moment.

For normal use, install it directly from GitHub:

```powershell
pip install "docscriptor @ git+https://github.com/Gonie-Gonie/docscriptor.git"
```

To upgrade later:

```powershell
pip install --upgrade "docscriptor @ git+https://github.com/Gonie-Gonie/docscriptor.git"
```

If you want to work from a repository checkout, run the bundled example scripts, or contribute locally:

```powershell
git clone https://github.com/Gonie-Gonie/docscriptor.git
cd docscriptor
pip install -e .
```

If you want the optional example dependencies from a local checkout:

```powershell
pip install -e ".[examples]"
```

For local development and tests:

```powershell
pip install -e ".[dev]"
```

On Windows, the repository also includes a helper that creates `.venv` and installs the development dependencies from the checkout:

```powershell
.\scripts\setup-repo.cmd
```

## Quick Start

```python
from docscriptor import Chapter, Document, DocumentSettings, Paragraph, Section, bold

report = Document(
    "Hello docscriptor",
    Chapter(
        "Getting Started",
        Section(
            "Overview",
            Paragraph(
                "This document was defined with ",
                bold("Python objects"),
                ".",
            ),
        ),
    ),
    settings=DocumentSettings(author="Docscriptor"),
)

report.save_docx("artifacts/hello.docx")
report.save_pdf("artifacts/hello.pdf")
report.save_html("artifacts/hello.html")
```

Document metadata and renderer defaults live under `DocumentSettings(...)`, so title matter and theme changes stay in one place.

## Authoring Model

Docscriptor tries to keep the source readable:

- create objects with classes such as `Document`, `Chapter`, `Section`, `Paragraph`, `Table`, and `Figure`
- apply inline actions with helpers such as `bold(...)`, `italic(...)`, `code(...)`, `Text.from_markup(...)`, `Comment.annotated(...)`, `Footnote.annotated(...)`, and `CitationSource.cite()`
- keep the document tree explicit so the Python structure matches the final output structure
- move document-wide metadata and theme options into `DocumentSettings(...)` when you want a single place to adjust title matter, cover pages, and renderer defaults

The default behavior is intentionally conventional:

- paragraphs are justified by default
- tables, figures, boxes, and their captions are centered by default
- headings are numbered as `1`, `1.1`, `1.1.1`, and so on
- ordered and bullet lists can be customized with `ListStyle(...)`
- heading numbering can be customized with `HeadingNumbering(...)`
- article-style front matter can be left unnumbered with `Section(..., numbered=False)`

## Features

- DOCX, PDF, and HTML rendering from the same document tree
- block objects for paragraphs, lists, code blocks, equations, boxes, tables, figures, and generated pages
- portable comments and footnotes that stay stable across DOCX, PDF, and HTML
- footnotes target page-bottom placement by default when the renderer supports it; `Theme(footnote_placement="document")` keeps the collected-notes pattern
- captioned tables and figures with automatic numbering and in-text references
- table support for `TableCell(...)`, `rowspan`, `colspan`, banded rows, and dataframe-like inputs
- figure support for both stored image files and `savefig()`-compatible Python objects
- fixed-layout `Sheet(...)` pages with positioned `TextBox(...)`, `ImageBox(...)`, basic `Shape(...)` objects, layer ordering, gradient-capable backgrounds, and standalone-page behavior for short forms such as certificates
- bibliography support through `CitationSource`, `CitationLibrary`, direct citation objects, and BibTeX import
- optional title matter such as subtitle, structured `Author(...)` metadata, `AuthorLayout(...)`, affiliations, and a cover page
- inline hyperlinks and heading/caption anchors for cross-references

## Example Scripts

The repository includes two standalone example directories:

- `examples/usage_guide_example/`
- `examples/journal_paper_example/`

Run them directly from the repository checkout:

```powershell
.\.venv\Scripts\python.exe .\examples\usage_guide_example\main.py
.\.venv\Scripts\python.exe .\examples\journal_paper_example\main.py
```

What they show:

- `usage_guide_example` is a detailed guide that keeps almost all assembly in one `main.py` so the source stays easy to read
- `journal_paper_example` shows a longer manuscript-style workflow with article-style sections, unnumbered abstract/highlights/acknowledgements, CSV-backed tables, and matplotlib figures inserted directly from Python objects

By default they write outputs under:

- `artifacts/usage-guide/`
- `artifacts/journal-paper/`

The main exported filenames are:

- `artifacts/usage-guide/docscriptor-user-guide.pdf`
- `artifacts/journal-paper/docscriptor-development-philosophy.pdf`

## Project Layout

The package is organized by responsibility:

- `src/docscriptor/document.py` for the root `Document`
- `src/docscriptor/settings.py` for `DocumentSettings` plus grouped configuration exports
- `src/docscriptor/components/` for the concrete authoring model (`base.py`, `blocks.py`, `equations.py`, `generated.py`, `inline.py`, `markup.py`, `media.py`, `people.py`, and `references.py`)
- `src/docscriptor/layout/` for low-level theme and indexing support
- `src/docscriptor/renderers/docx.py`, `src/docscriptor/renderers/pdf.py`, and `src/docscriptor/renderers/html.py` for format-specific layout

## Development

Assuming Python 3.14 is installed:

```powershell
.\scripts\setup-repo.cmd
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-repo.ps1
```

That setup script creates `.venv` and installs `.[dev]`.
If dependency metadata changes later, rerun the setup script or refresh the environment with:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Build distribution artifacts:

```powershell
.\.venv\Scripts\python.exe -m build
```

## Releases

Docscriptor versions are derived from git tags through `setuptools-scm`.

Create and push a release tag like this:

```powershell
.\scripts\release.ps1 0.3.0
```

That pushes `v0.3.0`, and the GitHub release workflow builds the wheel/sdist artifacts plus the two example PDFs and attaches them to the matching GitHub Release automatically.

If you want a curated release body instead of GitHub's generated notes, add a file such as `release-notes/v0.3.0.md` before pushing the tag.
