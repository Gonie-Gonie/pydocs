"""Document root object and renderer entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from docscriptor.blocks import BlockInput, Body
from docscriptor.core import PathLike
from docscriptor.inline import InlineInput, Text
from docscriptor.references import CitationLibrary, CitationSource, coerce_citation_library
from docscriptor.settings import DocumentSettings
from docscriptor.styles import Theme


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
        if settings is not None and any(
            value is not None
            for value in (
                author,
                summary,
                subtitle,
                authors,
                affiliations,
                theme,
            )
        ):
            raise ValueError(
                "Pass either settings=... or individual document settings, not both"
            )
        if settings is not None and cover_page:
            raise ValueError(
                "Pass cover_page via DocumentSettings when settings=... is used"
            )

        self.title = title
        self.body = body if body is not None else Body(*children)
        self.settings = settings or DocumentSettings(
            author=author,
            summary=summary,
            subtitle=subtitle,
            authors=authors,
            affiliations=affiliations,
            cover_page=cover_page,
            theme=theme,
        )
        self.citations = coerce_citation_library(citations)

    @property
    def author(self) -> str | None:
        return self.settings.author

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
    def authors(self) -> tuple[list[Text], ...]:
        return self.settings.authors

    @authors.setter
    def authors(self, value: tuple[list[Text], ...]) -> None:
        self.settings.authors = value

    @property
    def affiliations(self) -> tuple[list[Text], ...]:
        return self.settings.affiliations

    @affiliations.setter
    def affiliations(self, value: tuple[list[Text], ...]) -> None:
        self.settings.affiliations = value

    @property
    def cover_page(self) -> bool:
        return self.settings.cover_page

    @cover_page.setter
    def cover_page(self, value: bool) -> None:
        self.settings.cover_page = value

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
