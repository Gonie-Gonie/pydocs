"""User-facing configuration objects for documents and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from docscriptor.inline import InlineInput, Text, coerce_inlines
from docscriptor.styles import (
    BoxStyle,
    HeadingNumbering,
    ListStyle,
    ParagraphStyle,
    TableStyle,
    TextStyle,
    Theme,
)


@dataclass(slots=True, init=False)
class DocumentSettings:
    """Document-level metadata and rendering configuration."""

    author: str | None
    summary: str | None
    subtitle: list[Text] | None
    authors: tuple[list[Text], ...]
    affiliations: tuple[list[Text], ...]
    cover_page: bool
    theme: Theme

    def __init__(
        self,
        *,
        author: str | None = None,
        summary: str | None = None,
        subtitle: InlineInput | None = None,
        authors: Sequence[InlineInput] | None = None,
        affiliations: Sequence[InlineInput] | None = None,
        cover_page: bool = False,
        theme: Theme | None = None,
    ) -> None:
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


__all__ = [
    "BoxStyle",
    "DocumentSettings",
    "HeadingNumbering",
    "ListStyle",
    "ParagraphStyle",
    "TableStyle",
    "TextStyle",
    "Theme",
]
