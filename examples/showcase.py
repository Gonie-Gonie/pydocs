"""Generate a showcase document covering core docscriptor features."""

from __future__ import annotations

import base64
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


SAMPLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0tcAAAAASUVORK5CYII="
)


class CalloutParagraph(Paragraph):
    """A reusable paragraph subclass to demonstrate user extension."""

    def __init__(self, label: str, *content: object) -> None:
        super().__init__(
            Strong(f"{label}: "),
            *content,
            style=ParagraphStyle(space_after=14),
        )


def _write_sample_image(path: Path) -> None:
    path.write_bytes(SAMPLE_PNG)


def build_showcase(output_dir: str | Path) -> tuple[Path, Path]:
    """Build a showcase document and export it to DOCX and PDF."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_path = output_path / "showcase-image.png"
    _write_sample_image(image_path)

    report = Document(
        "Docscriptor Showcase",
        Section(
            "Authoring Model",
            CalloutParagraph(
                "Idea",
                "Compose documents with Python objects, then render the same structure into ",
                styled("DOCX", color="#004C99", bold=True),
                " and ",
                styled("PDF", color="#8A1C1C", bold=True),
                ".",
            ),
            Paragraph(
                "Inline styling can be mixed with helper parsing such as ",
                markup("**bold** text, *italic* text, and `code` fragments"),
                ".",
            ),
            Subsection(
                "Feature Checklist",
                bullet_list(
                    "Sections and subsections are regular Python instances.",
                    Paragraph(
                        "List items can also be explicit paragraphs with ",
                        styled("custom colors", color="#00856A"),
                        " and markup.",
                    ),
                    "Tables and figures render into both output formats.",
                ),
                numbered_list(
                    "Define the document tree.",
                    "Render DOCX for editing workflows.",
                    "Render PDF for distribution.",
                ),
            ),
            Subsection(
                "Structured Data",
                Table(
                    headers=["Capability", "Status"],
                    rows=[
                        ["Inline styling", "ready"],
                        ["Tables", "ready"],
                        ["Lists", "ready"],
                    ],
                    caption="Table 1. Current showcase capabilities.",
                    column_widths=[2.5, 2.0],
                ),
                figure(
                    image_path,
                    caption=Paragraph("Figure 1. Generated placeholder image."),
                    width_inches=1.2,
                ),
            ),
        ),
        author="docscriptor examples",
        summary="Feature showcase document",
    )

    docx_path = output_path / "docscriptor-showcase.docx"
    pdf_path = output_path / "docscriptor-showcase.pdf"
    report.save_docx(docx_path)
    report.save_pdf(pdf_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the showcase into the default example output directory."""

    docx_path, pdf_path = build_showcase(Path("artifacts") / "showcase")
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
