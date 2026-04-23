"""Document root object and renderer entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from docscriptor.blocks import BlockInput, Body
from docscriptor.core import PathLike
from docscriptor.inline import InlineInput, Text, coerce_inlines
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
    subtitle: list[Text] | None
    authors: tuple[list[Text], ...]
    affiliations: tuple[list[Text], ...]
    cover_page: bool
    theme: Theme
    citations: CitationLibrary

    def __init__(
        self,
        title: str,
        *children: BlockInput,
        body: Body | None = None,
        author: str | None = None,
        summary: str | None = None,
        subtitle: InlineInput | None = None,
        authors: Sequence[InlineInput] | None = None,
        affiliations: Sequence[InlineInput] | None = None,
        cover_page: bool = False,
        theme: Theme | None = None,
        citations: CitationLibrary | Sequence[CitationSource] | str | None = None,
    ) -> None:
        if body is not None and children:
            raise ValueError("Pass either body=... or positional blocks, not both")

        self.title = title
        self.body = body if body is not None else Body(*children)
        self.author = author
        self.summary = summary
        self.subtitle = coerce_inlines((subtitle,)) if subtitle is not None else None
        self.authors = tuple(
            coerce_inlines((entry,))
            for entry in (authors or ())
        )
        self.affiliations = tuple(
            coerce_inlines((entry,))
            for entry in (affiliations or ())
        )
        self.cover_page = cover_page
        self.theme = theme or Theme()
        self.citations = coerce_citation_library(citations)

    def split_top_level_children(self) -> tuple[list[object], list[object]]:
        """Split top-level blocks into front matter and main matter.

        Front matter is defined as every top-level block that appears before the
        first numbered level-1 heading.
        """

        for index, child in enumerate(self.body.children):
            level = getattr(child, "level", None)
            numbered = getattr(child, "numbered", False)
            if level == 1 and numbered:
                return self.body.children[:index], self.body.children[index:]
        return list(self.body.children), []

    def save_docx(self, path: PathLike) -> Path:
        """Render the document to DOCX and return the output path."""

        from docscriptor.renderers.docx import DocxRenderer

        return DocxRenderer().render(self, path)

    def save_pdf(self, path: PathLike) -> Path:
        """Render the document to PDF and return the output path."""

        from docscriptor.renderers.pdf import PdfRenderer

        return PdfRenderer().render(self, path)
