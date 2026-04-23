"""Bibliography objects and citation library helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING, Sequence

from docscriptor.core import DocscriptorError

if TYPE_CHECKING:
    from docscriptor.inline import Citation, Text
    from docscriptor.styles import TextStyle


@dataclass(slots=True, init=False)
class CitationSource:
    """Structured bibliography metadata for a single reference entry."""

    title: str
    key: str | None
    authors: tuple[str, ...] = ()
    organization: str | None = None
    publisher: str | None = None
    year: str | None = None
    url: str | None = None
    note: str | None = None

    def __init__(
        self,
        title: str,
        *,
        key: str | None = None,
        authors: Sequence[str] = (),
        organization: str | None = None,
        publisher: str | None = None,
        year: str | None = None,
        url: str | None = None,
        note: str | None = None,
    ) -> None:
        self.title = title
        self.key = key
        self.authors = tuple(authors)
        self.organization = organization
        self.publisher = publisher
        self.year = year
        self.url = url
        self.note = note

    def format_reference(self) -> str:
        """Format the entry as a plain bibliography string."""

        segments: list[str] = []
        if self.authors:
            segments.append(", ".join(self.authors))
        elif self.organization:
            segments.append(self.organization)
        segments.append(self.title)
        if self.publisher:
            segments.append(self.publisher)
        if self.year:
            segments.append(self.year)
        if self.url:
            segments.append(self.url)
        if self.note:
            segments.append(self.note)
        cleaned = [segment.strip().rstrip(".") for segment in segments if segment]
        return ". ".join(cleaned) + "."

    def reference_fragments(self) -> list[Text]:
        """Return renderer-friendly inline fragments for a reference entry."""

        from docscriptor.inline import Hyperlink, Text

        fragments: list[Text] = []
        text_segments: list[str] = []
        if self.authors:
            text_segments.append(", ".join(self.authors))
        elif self.organization:
            text_segments.append(self.organization)
        text_segments.append(self.title)
        if self.publisher:
            text_segments.append(self.publisher)
        if self.year:
            text_segments.append(self.year)
        prefix = ". ".join(
            segment.strip().rstrip(".")
            for segment in text_segments
            if segment
        )
        if prefix:
            fragments.append(Text(f"{prefix}. "))
        if self.url:
            fragments.append(Hyperlink.external(self.url, self.url))
            if self.note:
                fragments.append(Text(f". {self.note.strip().rstrip('.')}."))
            else:
                fragments.append(Text("."))
            return fragments
        if self.note:
            fragments.append(Text(f"{self.note.strip().rstrip('.')}."))
        elif not fragments:
            fragments.append(Text(""))
        return fragments

    def cite(self, *, style: TextStyle | None = None) -> Citation:
        """Create an inline citation that points to this source."""

        from docscriptor.inline import Citation

        return Citation.reference(self, style=style)


@dataclass(slots=True)
class CitationLibrary:
    """Registry of bibliography entries addressable by citation key."""

    entries: dict[str, CitationSource] = field(default_factory=dict)

    def __init__(self, entries: Sequence[CitationSource] | None = None) -> None:
        self.entries = {}
        if entries is not None:
            for entry in entries:
                self.add(entry)

    def add(self, entry: CitationSource) -> None:
        """Register a citation source under its key."""

        if not entry.key:
            raise DocscriptorError(
                "CitationSource.key is required when adding entries to a CitationLibrary"
            )
        if entry.key in self.entries:
            raise DocscriptorError(f"Duplicate citation key: {entry.key!r}")
        self.entries[entry.key] = entry

    def resolve(self, key: str) -> CitationSource:
        """Resolve a registered citation key to a source entry."""

        if key not in self.entries:
            raise DocscriptorError(f"Unknown citation key: {key!r}")
        return self.entries[key]

    def cite(self, key: str, *, style: TextStyle | None = None) -> Citation:
        """Create an inline citation from a registered citation key."""

        from docscriptor.inline import Citation

        return Citation.reference(key, style=style)

    @classmethod
    def from_bibtex(cls, source: str) -> CitationLibrary:
        """Parse BibTeX text into a citation library."""

        entries: list[CitationSource] = []
        for key, fields in _parse_bibtex_entries(source):
            authors = tuple(
                part.strip()
                for part in fields.get("author", "").split(" and ")
                if part.strip()
            )
            entries.append(
                CitationSource(
                    title=fields.get("title", key),
                    key=key,
                    authors=authors,
                    organization=fields.get("organization") or fields.get("institution"),
                    publisher=(
                        fields.get("publisher")
                        or fields.get("journal")
                        or fields.get("booktitle")
                        or fields.get("howpublished")
                    ),
                    year=fields.get("year"),
                    url=fields.get("url"),
                    note=fields.get("note"),
                )
            )
        return cls(entries)


def coerce_citation_library(
    value: CitationLibrary | Sequence[CitationSource] | str | None,
) -> CitationLibrary:
    """Normalize any supported citation input into a ``CitationLibrary``."""

    if value is None:
        return CitationLibrary()
    if isinstance(value, CitationLibrary):
        return value
    if isinstance(value, str):
        return CitationLibrary.from_bibtex(value)
    return CitationLibrary(value)


def _parse_bibtex_entries(source: str) -> list[tuple[str, dict[str, str]]]:
    entries: list[tuple[str, dict[str, str]]] = []
    cursor = 0

    while True:
        match = re.search(r"@\w+\s*\{", source[cursor:])
        if match is None:
            break
        entry_start = cursor + match.start()
        body_start = entry_start + match.group(0).rfind("{") + 1
        depth = 1
        position = body_start
        while position < len(source) and depth > 0:
            char = source[position]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            position += 1
        body = source[body_start : position - 1].strip()
        cursor = position
        if not body:
            continue

        key, _, fields_text = body.partition(",")
        fields = _parse_bibtex_fields(fields_text)
        entries.append((key.strip(), fields))

    return entries


def _parse_bibtex_fields(source: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in _split_bibtex_fields(source):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cleaned = value.strip().rstrip(",").strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        fields[key.strip().lower()] = cleaned.strip()
    return fields


def _split_bibtex_fields(source: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []

    for char in source:
        if char == "{":
            depth += 1
        elif char == "}":
            depth = max(depth - 1, 0)

        if char == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(char)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts
