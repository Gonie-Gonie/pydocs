"""Generate a showcase document covering core docscriptor features."""

from __future__ import annotations

from pathlib import Path

from docscriptor import (
    Document,
    Paragraph,
    ParagraphStyle,
    Section,
    Strong,
    Subsection,
    Table,
    bullet_list,
    figure,
    markup,
    numbered_list,
    styled,
)


EXAMPLE_DIR = Path(__file__).resolve().parent
ASSET_DIR = EXAMPLE_DIR / "assets"
SHOWCASE_IMAGE = ASSET_DIR / "showcase-figure.png"
OUTPUT_DIR = Path("artifacts") / "showcase"

AUTHORING_MODEL_INTRO = Paragraph(
    Strong("Idea: "),
    "Compose documents with Python objects, then render the same structure into ",
    styled("DOCX", color="#004C99", bold=True),
    " and ",
    styled("PDF", color="#8A1C1C", bold=True),
    ".",
    style=ParagraphStyle(space_after=14),
)

INLINE_STYLING_EXAMPLE = Paragraph(
    "Inline styling can be mixed with helper parsing such as ",
    markup("**bold** text, *italic* text, and `code` fragments"),
    ".",
)

FEATURE_CHECKLIST = bullet_list(
    "Sections and subsections are regular Python instances.",
    Paragraph(
        "List items can also be explicit paragraphs with ",
        styled("custom colors", color="#00856A"),
        " and markup.",
    ),
    "Tables and figures render into both output formats.",
)

RENDER_STEPS = numbered_list(
    "Define the document tree.",
    "Render DOCX for editing workflows.",
    "Render PDF for distribution.",
)

CAPABILITY_TABLE = Table(
    headers=["Capability", "Status"],
    rows=[
        ["Inline styling", "ready"],
        ["Tables", "ready"],
        ["Lists", "ready"],
    ],
    caption="Table 1. Current showcase capabilities.",
    column_widths=[2.5, 2.0],
)

SHOWCASE_FIGURE = figure(
    SHOWCASE_IMAGE,
    caption=Paragraph("Figure 1. Bundled showcase image."),
    width_inches=4.2,
)

SHOWCASE_DOCUMENT = Document(
    "Docscriptor Showcase",
    Section(
        "Authoring Model",
        AUTHORING_MODEL_INTRO,
        INLINE_STYLING_EXAMPLE,
        Subsection(
            "Feature Checklist",
            FEATURE_CHECKLIST,
            RENDER_STEPS,
        ),
        Subsection(
            "Structured Data",
            CAPABILITY_TABLE,
            SHOWCASE_FIGURE,
        ),
    ),
    author="docscriptor examples",
    summary="Feature showcase document",
)


def build_showcase(output_dir: str | Path) -> tuple[Path, Path]:
    """Build a showcase document and export it to DOCX and PDF."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    docx_path = output_path / "docscriptor-showcase.docx"
    pdf_path = output_path / "docscriptor-showcase.pdf"
    SHOWCASE_DOCUMENT.save_docx(docx_path)
    SHOWCASE_DOCUMENT.save_pdf(pdf_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the showcase into the default example output directory."""

    docx_path, pdf_path = build_showcase(OUTPUT_DIR)
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
