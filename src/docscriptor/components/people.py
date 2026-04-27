"""Structured people and affiliation metadata for title matter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from docscriptor.components.inline import Hyperlink, Text


@dataclass(slots=True)
class Affiliation:
    """Structured affiliation metadata for an author."""

    label: str | None = None
    department: str | None = None
    organization: str | None = None
    city: str | None = None
    country: str | None = None

    def __post_init__(self) -> None:
        if not any(
            (
                self.label,
                self.department,
                self.organization,
                self.city,
                self.country,
            )
        ):
            raise ValueError("Affiliation requires at least one populated field")

    def formatted(self) -> str:
        """Return a single-line affiliation label."""

        if self.label is not None:
            return self.label
        return ", ".join(
            part
            for part in (
                self.department,
                self.organization,
                self.city,
                self.country,
            )
            if part
        )


AffiliationInput = Affiliation | str


@dataclass(slots=True)
class AuthorLayout:
    """Configurable title-matter layout for structured author metadata."""

    mode: str = "journal"
    show_affiliations: bool = True
    show_details: bool = True
    name_separator: str = ", "
    affiliation_label_format: str = "[{label}]"
    corresponding_marker: str = "*"

    def __post_init__(self) -> None:
        if self.mode not in {"journal", "stacked"}:
            raise ValueError(f"Unsupported author layout mode: {self.mode!r}")
        if "{label}" not in self.affiliation_label_format:
            raise ValueError(
                "author affiliation_label_format must contain a '{label}' placeholder"
            )


@dataclass(slots=True, frozen=True)
class AuthorTitleLine:
    """A typed title-matter line derived from a structured author."""

    kind: str
    fragments: tuple[Text, ...]

    def __post_init__(self) -> None:
        if self.kind not in {"name", "affiliation", "detail"}:
            raise ValueError(f"Unsupported author title line kind: {self.kind!r}")
        if not self.fragments:
            raise ValueError("AuthorTitleLine.fragments must not be empty")


@dataclass(slots=True, init=False)
class Author:
    """Structured author metadata for title matter and document metadata."""

    name: str
    affiliations: tuple[Affiliation, ...]
    email: str | None
    position: str | None
    corresponding: bool
    orcid: str | None
    note: str | None

    def __init__(
        self,
        name: str,
        *,
        affiliations: Sequence[AffiliationInput] | None = None,
        email: str | None = None,
        position: str | None = None,
        corresponding: bool = False,
        orcid: str | None = None,
        note: str | None = None,
    ) -> None:
        self.name = name
        self.affiliations = tuple(
            value if isinstance(value, Affiliation) else Affiliation(label=value)
            for value in (affiliations or ())
        )
        self.email = email
        self.position = position
        self.corresponding = corresponding
        self.orcid = orcid
        self.note = note

    def display_name(self) -> str:
        """Return the visible author label."""

        return self.name

    def title_lines(
        self,
        *,
        corresponding_marker: str = "*",
        show_affiliations: bool = True,
        show_details: bool = True,
    ) -> tuple[AuthorTitleLine, ...]:
        """Return renderer-ready title-matter lines for this author."""

        lines: list[AuthorTitleLine] = [
            AuthorTitleLine(
                "name",
                (Text(self.display_name_with_marker(corresponding_marker)),),
            )
        ]
        if show_affiliations:
            for affiliation in self.affiliations:
                lines.append(
                    AuthorTitleLine(
                        "affiliation",
                        (Text(affiliation.formatted()),),
                    )
                )
        detail = self.detail_fragments()
        if show_details and detail is not None:
            lines.append(AuthorTitleLine("detail", tuple(detail)))
        return tuple(lines)

    def display_name_with_marker(self, marker: str = "*") -> str:
        """Return the visible author label with the corresponding marker when needed."""

        if self.corresponding and marker:
            return f"{self.name}{marker}"
        return self.name

    def detail_fragments(self) -> list[Text] | None:
        """Return supplemental detail fragments for title matter."""

        fragments: list[Text] = []

        def append_separator() -> None:
            if fragments:
                fragments.append(Text(" | "))

        if self.position:
            append_separator()
            fragments.append(Text(self.position))
        if self.email:
            append_separator()
            fragments.append(Hyperlink.external(f"mailto:{self.email}", self.email))
        if self.orcid:
            append_separator()
            normalized_orcid = self.orcid.removeprefix("https://orcid.org/").strip("/")
            fragments.append(Text("ORCID "))
            fragments.append(
                Hyperlink.external(
                    f"https://orcid.org/{normalized_orcid}",
                    normalized_orcid,
                )
            )
        if self.note:
            append_separator()
            fragments.append(Text(self.note))
        return fragments or None


AuthorInput = Author | str


def coerce_authors(values: Sequence[AuthorInput] | None) -> tuple[Author, ...]:
    """Normalize simple author inputs into structured authors."""

    if values is None:
        return ()
    return tuple(
        value if isinstance(value, Author) else Author(str(value))
        for value in values
    )


def coerce_author_layout(value: AuthorLayout | None) -> AuthorLayout:
    """Normalize document author-layout configuration."""

    return value if value is not None else AuthorLayout()


__all__ = [
    "Affiliation",
    "AffiliationInput",
    "Author",
    "AuthorInput",
    "AuthorLayout",
    "AuthorTitleLine",
    "coerce_author_layout",
    "coerce_authors",
]
