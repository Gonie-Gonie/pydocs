# docscriptor

Docscriptor is an early-stage, Python-first alternative to LaTeX for teams who want documents to be defined with regular Python code.
The long-term goal is to compose structured content in scripts, reuse templates and components, and render the same source into PDF and DOCX outputs.

## Vision

- define documents with normal Python modules, functions, and data structures
- make document generation programmable, testable, and reusable
- support multiple export targets without committing to a TeX-centric workflow

## Current Structure

The package now ships with a basic document object model and two renderers:

- block objects such as `Document`, `Body`, `Section`, `Subsection`, `Paragraph`, `Table`, and `Figure`
- inline objects such as `Text`, `Strong`, `Emphasis`, `Code`, and `styled(...)`
- list objects through `bullet_list(...)`, `numbered_list(...)`, and `ListBlock`
- a lightweight `markup(...)` helper for markdown-like inline bold, italic, and code formatting
- render targets for `.docx` and `.pdf`

## Authoring Model

The intended workflow is:

1. define a document tree with Python instances
2. subclass the provided building blocks when you want reusable semantics
3. render the same tree into one or more output formats

The core model in `docscriptor.model` is intentionally class-based so users can build their own abstractions on top.
For example, a team can subclass `Paragraph`, `Section`, or `Document` to create house styles, reusable callouts, or report templates.

```python
from docscriptor import Paragraph, ParagraphStyle, Strong


class WarningParagraph(Paragraph):
    def __init__(self, *content):
        super().__init__(
            Strong("Warning: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )
```

Example:

```python
from docscriptor import (
    Document,
    Figure,
    Paragraph,
    Section,
    Subsection,
    Table,
    markup,
    styled,
)

report = Document(
    "Experiment Report",
    Section(
        "Overview",
        Paragraph(
            "This document was written in Python with ",
            styled("custom colors", color="#0055AA"),
            " and ",
            markup("**lightweight** *markup* support."),
        ),
        Subsection(
            "Measurements",
            Table(
                headers=["Metric", "Value"],
                rows=[
                    ["Latency", "14 ms"],
                    ["Success rate", "99.8%"],
                ],
                caption="Table 1. Summary metrics.",
            ),
        ),
        Figure("example.png", caption=Paragraph("Figure 1. Example output."), width_inches=3.0),
    ),
    author="Docscriptor",
)

report.save_docx("artifacts/report.docx")
report.save_pdf("artifacts/report.pdf")
```

## Example Script

The repository also includes a runnable showcase script that exercises sections, inline styling, bullet lists, numbered lists, tables, figures, and subclassing:

```powershell
python -m examples.showcase
```

By default it writes these files under `artifacts/showcase/`:

- `docscriptor-showcase.docx`
- `docscriptor-showcase.pdf`
- `showcase-image.png`

This example is also covered by automated tests so the generated outputs are checked continuously.

## Development

Assuming Python 3.14 is already installed on the machine, run the setup script:

```powershell
.\setup.ps1
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
After running `.\setup.ps1`, opening the folder in VS Code should pick `.venv` as the default interpreter and enable pytest discovery for the `tests` folder.

Run the test suite:

```powershell
pytest
```

Build distribution artifacts:

```powershell
python -m build
```
