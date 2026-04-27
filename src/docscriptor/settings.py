"""User-facing configuration objects for documents and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from docscriptor.components.inline import InlineInput, Text, coerce_inlines
from docscriptor.components.people import (
    Affiliation,
    Author,
    AuthorInput,
    AuthorLayout,
    AuthorTitleLine,
    coerce_author_layout,
    coerce_authors,
)
from docscriptor.layout.theme import (
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
    authors: tuple[Author, ...]
    author_layout: AuthorLayout
    cover_page: bool
    theme: Theme

    def __init__(
        self,
        *,
        author: str | None = None,
        summary: str | None = None,
        subtitle: InlineInput | None = None,
        authors: Sequence[AuthorInput] | None = None,
        author_layout: AuthorLayout | None = None,
        cover_page: bool = False,
        theme: Theme | None = None,
    ) -> None:
        self.author = author
        self.summary = summary
        self.subtitle = coerce_inlines((subtitle,)) if subtitle is not None else None
        self.authors = coerce_authors(authors)
        self.author_layout = coerce_author_layout(author_layout)
        self.cover_page = cover_page
        self.theme = theme or Theme()

    def resolved_author(self) -> str | None:
        """Return the metadata author string used in file properties."""

        if self.author is not None:
            return self.author
        if not self.authors:
            return None
        return "; ".join(author.name for author in self.authors)

    def iter_author_title_lines(self) -> Iterable[tuple[AuthorTitleLine, bool]]:
        """Yield author title lines together with author-boundary markers."""

        if self.author_layout.mode == "stacked":
            yield from self._iter_stacked_author_title_lines()
            return
        yield from self._iter_journal_author_title_lines()

    def _iter_stacked_author_title_lines(self) -> Iterable[tuple[AuthorTitleLine, bool]]:
        for author in self.authors:
            lines = author.title_lines(
                corresponding_marker=self.author_layout.corresponding_marker,
                show_affiliations=self.author_layout.show_affiliations,
                show_details=self.author_layout.show_details,
            )
            for index, line in enumerate(lines):
                yield line, index == len(lines) - 1

    def _iter_journal_author_title_lines(self) -> Iterable[tuple[AuthorTitleLine, bool]]:
        if not self.authors:
            return

        affiliation_numbers: dict[str, int] = {}
        ordered_affiliations: list[str] = []
        for author in self.authors:
            for affiliation in author.affiliations:
                label = affiliation.formatted()
                if label not in affiliation_numbers:
                    affiliation_numbers[label] = len(ordered_affiliations) + 1
                    ordered_affiliations.append(label)

        name_fragments: list[Text] = []
        for index, author in enumerate(self.authors):
            if index:
                name_fragments.append(Text(self.author_layout.name_separator))
            markers = [
                str(affiliation_numbers[affiliation.formatted()])
                for affiliation in author.affiliations
            ]
            suffix = ""
            if markers:
                suffix += " " + self.author_layout.affiliation_label_format.format(
                    label=",".join(markers)
                )
            if author.corresponding and self.author_layout.corresponding_marker:
                suffix += self.author_layout.corresponding_marker
            name_fragments.append(Text(f"{author.name}{suffix}"))
        lines: list[AuthorTitleLine] = [
            AuthorTitleLine("name", tuple(name_fragments))
        ]

        if self.author_layout.show_affiliations:
            for affiliation in ordered_affiliations:
                label = affiliation_numbers[affiliation]
                lines.append(
                    AuthorTitleLine(
                        "affiliation",
                        (
                            Text(
                                f"{self.author_layout.affiliation_label_format.format(label=label)} {affiliation}"
                            ),
                        ),
                    )
                )

        if self.author_layout.show_details:
            for author in self.authors:
                detail_fragments = author.detail_fragments()
                if detail_fragments is None:
                    continue
                lines.append(
                    AuthorTitleLine(
                        "detail",
                        (Text(f"{author.name}: "), *detail_fragments),
                    )
                )

        if (
            self.author_layout.corresponding_marker
            and any(author.corresponding for author in self.authors)
        ):
            corresponding_names = ", ".join(
                author.name for author in self.authors if author.corresponding
            )
            lines.insert(
                1 + len(ordered_affiliations) if self.author_layout.show_affiliations else 1,
                AuthorTitleLine(
                    "detail",
                    (
                        Text(
                            f"{self.author_layout.corresponding_marker} Corresponding author: {corresponding_names}"
                        ),
                    ),
                ),
            )

        for index, line in enumerate(lines):
            yield line, index == len(lines) - 1


__all__ = [
    "Affiliation",
    "Author",
    "AuthorLayout",
    "BoxStyle",
    "DocumentSettings",
    "HeadingNumbering",
    "ListStyle",
    "ParagraphStyle",
    "TableStyle",
    "TextStyle",
    "Theme",
]
