"""Document root object and renderer entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from docscriptor.components.base import BlockInput, Body
from docscriptor.components.inline import Text
from docscriptor.components.people import Author, AuthorInput, coerce_authors
from docscriptor.components.references import CitationLibrary, CitationSource, coerce_citation_library
from docscriptor.core import PathLike
from docscriptor.layout.theme import Theme
from docscriptor.settings import DocumentSettings


@dataclass(slots=True, init=False)
class Document:
    """Top-level renderable document.

    Args:
        title: Document title rendered at the top of the output.
        *children: Top-level blocks. Mutually exclusive with ``body=...``.
        body: Optional pre-built ``Body`` container.
        settings: Optional grouped document metadata and rendering settings.
        citations: Bibliography metadata supplied as a library, a sequence of
            ``CitationSource`` objects, or BibTeX text.
    """

    title: str
    body: Body
    settings: DocumentSettings
    citations: CitationLibrary

    def __init__(
        self,
        title: str,
        *children: BlockInput,
        body: Body | None = None,
        settings: DocumentSettings | None = None,
        citations: CitationLibrary | Sequence[CitationSource] | str | None = None,
    ) -> None:
        if body is not None and children:
            raise ValueError("Pass either body=... or positional blocks, not both")

        self.title = title
        self.body = body if body is not None else Body(*children)
        self.settings = settings or DocumentSettings()
        self.citations = coerce_citation_library(citations)

    @property
    def author(self) -> str | None:
        return self.settings.resolved_author()

    @author.setter
    def author(self, value: str | None) -> None:
        self.settings.author = value

    @property
    def summary(self) -> str | None:
        return self.settings.summary

    @summary.setter
    def summary(self, value: str | None) -> None:
        self.settings.summary = value

    @property
    def subtitle(self) -> list[Text] | None:
        return self.settings.subtitle

    @subtitle.setter
    def subtitle(self, value: list[Text] | None) -> None:
        self.settings.subtitle = value

    @property
    def authors(self) -> tuple[Author, ...]:
        return self.settings.authors

    @authors.setter
    def authors(self, value: Sequence[AuthorInput]) -> None:
        self.settings.authors = coerce_authors(value)

    @property
    def cover_page(self) -> bool:
        return self.settings.cover_page

    @cover_page.setter
    def cover_page(self, value: bool) -> None:
        self.settings.cover_page = value

    @property
    def unit(self) -> str:
        return self.settings.unit

    @unit.setter
    def unit(self, value: str) -> None:
        from docscriptor.core import normalize_length_unit

        self.settings.unit = normalize_length_unit(value)

    def get_page_width(self, scale: float = 1.0, *, unit: str | None = None) -> float:
        return self.settings.get_page_width(scale, unit=unit)

    def get_page_height(self, scale: float = 1.0, *, unit: str | None = None) -> float:
        return self.settings.get_page_height(scale, unit=unit)

    def get_text_width(self, scale: float = 1.0, *, unit: str | None = None) -> float:
        return self.settings.get_text_width(scale, unit=unit)

    def get_text_height(self, scale: float = 1.0, *, unit: str | None = None) -> float:
        return self.settings.get_text_height(scale, unit=unit)

    @property
    def theme(self) -> Theme:
        return self.settings.theme

    @theme.setter
    def theme(self, value: Theme) -> None:
        self.settings.theme = value

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

    def save_html(self, path: PathLike) -> Path:
        """Render the document to HTML and return the output path."""

        from docscriptor.renderers.html import HtmlRenderer

        return HtmlRenderer().render(self, path)
