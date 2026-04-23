"""Document root object and renderer entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from docscriptor.blocks import BlockInput, Body
from docscriptor.core import PathLike
from docscriptor.references import CitationLibrary, CitationSource, coerce_citation_library
from docscriptor.styles import Theme


@dataclass(slots=True, init=False)
class Document:
    """Top-level renderable document.

    Args:
        title: Document title rendered at the top of the output.
        *children: Top-level blocks. Mutually exclusive with ``body=...``.
        body: Optional pre-built ``Body`` container.
        author: Optional author metadata.
        summary: Optional summary or subject metadata.
        theme: Document-wide renderer defaults.
        citations: Bibliography metadata supplied as a library, a sequence of
            ``CitationSource`` objects, or BibTeX text.
    """

    title: str
    body: Body
    author: str | None
    summary: str | None
    theme: Theme
    citations: CitationLibrary

    def __init__(
        self,
        title: str,
        *children: BlockInput,
        body: Body | None = None,
        author: str | None = None,
        summary: str | None = None,
        theme: Theme | None = None,
        citations: CitationLibrary | Sequence[CitationSource] | str | None = None,
    ) -> None:
        if body is not None and children:
            raise ValueError("Pass either body=... or positional blocks, not both")

        self.title = title
        self.body = body if body is not None else Body(*children)
        self.author = author
        self.summary = summary
        self.theme = theme or Theme()
        self.citations = coerce_citation_library(citations)

    def save_docx(self, path: PathLike) -> Path:
        """Render the document to DOCX and return the output path."""

        from docscriptor.renderers.docx import DocxRenderer

        return DocxRenderer().render(self, path)

    def save_pdf(self, path: PathLike) -> Path:
        """Render the document to PDF and return the output path."""

        from docscriptor.renderers.pdf import PdfRenderer

        return PdfRenderer().render(self, path)
