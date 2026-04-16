"""Core document model for docscriptor."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable, Sequence


PathLike = str | Path


class DocscriptorError(Exception):
    """Raised when a document structure cannot be rendered."""


def _normalize_color(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lstrip("#").upper()
    if len(normalized) != 6 or any(char not in "0123456789ABCDEF" for char in normalized):
        raise ValueError(f"Expected a 6-digit hex color, got: {value!r}")
    return normalized


@dataclass(slots=True)
class TextStyle:
    """Inline text styling."""

    font_name: str | None = None
    font_size: float | None = None
    color: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None

    def __post_init__(self) -> None:
        self.color = _normalize_color(self.color)

    def merged(self, *others: TextStyle | None) -> TextStyle:
        merged = TextStyle(
            font_name=self.font_name,
            font_size=self.font_size,
            color=self.color,
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
        )
        for other in others:
            if other is None:
                continue
            for field_name in ("font_name", "font_size", "color", "bold", "italic", "underline"):
                value = getattr(other, field_name)
                if value is not None:
                    setattr(merged, field_name, value)
        return merged


@dataclass(slots=True)
class ParagraphStyle:
    """Block-level paragraph styling."""

    alignment: str = "left"
    space_after: float | None = 12.0
    leading: float | None = None

    def __post_init__(self) -> None:
        if self.alignment not in {"left", "center", "right", "justify"}:
            raise ValueError(f"Unsupported alignment: {self.alignment!r}")


@dataclass(slots=True)
class Theme:
    """Default document theme used by renderers."""

    body_font_name: str = "Times New Roman"
    monospace_font_name: str = "Courier New"
    title_font_size: float = 22.0
    body_font_size: float = 11.0
    heading_sizes: tuple[float, ...] = (18.0, 15.0, 13.0, 11.5)
    caption_font_size: float = 9.0
    table_label: str = "Table"
    figure_label: str = "Figure"
    list_of_tables_title: str = "List of Tables"
    list_of_figures_title: str = "List of Figures"
    references_title: str = "References"
    contents_title: str = "Contents"
    generated_section_level: int = 2

    def heading_size(self, level: int) -> float:
        index = min(max(level - 1, 0), len(self.heading_sizes) - 1)
        return self.heading_sizes[index]

    def heading_emphasis(self, level: int) -> tuple[bool, bool]:
        emphasis = (
            (True, False),
            (True, False),
            (True, True),
            (False, True),
        )
        index = min(max(level - 1, 0), len(emphasis) - 1)
        return emphasis[index]

    def heading_alignment(self, level: int) -> str:
        return "center" if level == 1 else "left"


@dataclass(slots=True)
class Text:
    """Inline text fragment."""

    value: str
    style: TextStyle = field(default_factory=TextStyle)

    def plain_text(self) -> str:
        return self.value


class Bold(Text):
    """Bold inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(bold=True).merged(style))


class Italic(Text):
    """Italic inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(italic=True).merged(style))


class Monospace(Text):
    """Monospace inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(font_name="Courier New").merged(style))


Strong = Bold
Emphasis = Italic
Code = Monospace


class _BlockReference(Text):
    """Inline reference to a numbered table or figure."""

    __slots__ = ("target",)

    def __init__(self, target: Table | Figure, style: TextStyle | None = None) -> None:
        super().__init__(value="", style=style or TextStyle())
        self.target = target

    def plain_text(self) -> str:
        label = "Table" if isinstance(self.target, Table) else "Figure"
        return f"{label} ?"


class Citation(Text):
    """Inline citation rendered from a bibliography entry."""

    __slots__ = ("target",)

    def __init__(self, target: CitationSource | str, style: TextStyle | None = None) -> None:
        super().__init__(value="", style=style or TextStyle())
        self.target = target

    def plain_text(self) -> str:
        return "[?]"


def cite(target: CitationSource | str, *, style: TextStyle | None = None) -> Citation:
    """Create an inline citation for a bibliography entry or registered key."""

    return Citation(target, style=style)


def styled(value: str, **style_values: object) -> Text:
    """Create a styled inline fragment."""

    return Text(value=value, style=TextStyle(**style_values))


InlineInput = Text | str | Sequence["InlineInput"] | None


def coerce_inlines(values: Iterable[InlineInput]) -> list[Text]:
    """Normalize inline inputs into Text fragments."""

    normalized: list[Text] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, Text):
            normalized.append(value)
            continue
        if isinstance(value, (Table, Figure)):
            normalized.append(_BlockReference(value))
            continue
        if isinstance(value, str):
            normalized.append(Text(value))
            continue
        if isinstance(value, Sequence):
            normalized.extend(coerce_inlines(value))
            continue
        raise TypeError(f"Unsupported inline value: {type(value)!r}")
    return normalized


class Block:
    """Marker base class for block-level document objects."""


@dataclass(slots=True, init=False)
class Paragraph(Block):
    """A paragraph made of styled inline fragments."""

    content: list[Text]
    style: ParagraphStyle

    def __init__(self, *content: InlineInput, style: ParagraphStyle | None = None) -> None:
        self.content = coerce_inlines(content)
        self.style = style or ParagraphStyle()

    def plain_text(self) -> str:
        return "".join(fragment.plain_text() for fragment in self.content)


ListInput = Paragraph | InlineInput


def coerce_list_item(value: ListInput) -> Paragraph:
    """Normalize a list item into a Paragraph instance."""

    if isinstance(value, Paragraph):
        return value
    return Paragraph(value)


@dataclass(slots=True, init=False)
class _ListBlock(Block):
    """Internal base class for list-style blocks."""

    items: list[Paragraph]
    ordered: bool

    def __init__(self, *items: ListInput, ordered: bool = False) -> None:
        self.items = [coerce_list_item(item) for item in items if item is not None]
        self.ordered = ordered


class BulletList(_ListBlock):
    """An unordered list of paragraphs."""

    def __init__(self, *items: ListInput) -> None:
        super().__init__(*items, ordered=False)


class NumberedList(_ListBlock):
    """An ordered list of paragraphs."""

    def __init__(self, *items: ListInput) -> None:
        super().__init__(*items, ordered=True)


@dataclass(slots=True)
class CodeBlock(Block):
    """A block-level preformatted code snippet."""

    code: str
    language: str | None = None
    style: ParagraphStyle = field(default_factory=lambda: ParagraphStyle(space_after=12.0))


@dataclass(slots=True, init=False)
class TableList(Block):
    """Generated list of numbered tables."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None


@dataclass(slots=True, init=False)
class FigureList(Block):
    """Generated list of numbered figures."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None


@dataclass(slots=True, init=False)
class ReferencesPage(Block):
    """Generated reference page for cited bibliography entries."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None


@dataclass(slots=True, init=False)
class TableOfContents(Block):
    """Generated outline of chapter and section titles."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None


BlockInput = Block | str | Sequence["BlockInput"] | None


def coerce_blocks(values: Iterable[BlockInput]) -> list[Block]:
    """Normalize block inputs into block instances."""

    normalized: list[Block] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, Block):
            normalized.append(value)
            continue
        if isinstance(value, str):
            normalized.append(Paragraph(value))
            continue
        if isinstance(value, Sequence):
            normalized.extend(coerce_blocks(value))
            continue
        raise TypeError(f"Unsupported block value: {type(value)!r}")
    return normalized


@dataclass(slots=True, init=False)
class Body(Block):
    """Top-level block container."""

    children: list[Block]

    def __init__(self, *children: BlockInput) -> None:
        self.children = coerce_blocks(children)


@dataclass(slots=True, init=False)
class Section(Block):
    """A titled section containing nested blocks."""

    title: list[Text]
    children: list[Block]
    level: int

    def __init__(self, title: InlineInput, *children: BlockInput, level: int = 2) -> None:
        if level < 1:
            raise ValueError("Section level must be >= 1")
        self.title = coerce_inlines((title,))
        self.children = coerce_blocks(children)
        self.level = level

    def plain_title(self) -> str:
        return "".join(fragment.plain_text() for fragment in self.title)


class Chapter(Section):
    """First-level document division."""

    def __init__(self, title: InlineInput, *children: BlockInput) -> None:
        super().__init__(title, *children, level=1)


class Subsection(Section):
    """Third-level document division."""

    def __init__(self, title: InlineInput, *children: BlockInput) -> None:
        super().__init__(title, *children, level=3)


class Subsubsection(Section):
    """Fourth-level document division."""

    def __init__(self, title: InlineInput, *children: BlockInput) -> None:
        super().__init__(title, *children, level=4)


CellInput = Paragraph | InlineInput


def coerce_cell(value: CellInput) -> Paragraph:
    if isinstance(value, Paragraph):
        return value
    return Paragraph(value)


@dataclass(slots=True, init=False)
class Table(Block):
    """A simple text table with optional caption."""

    headers: list[Paragraph]
    rows: list[list[Paragraph]]
    caption: Paragraph | None
    column_widths: list[float] | None
    identifier: str | None

    def __init__(
        self,
        headers: Sequence[CellInput],
        rows: Sequence[Sequence[CellInput]],
        *,
        caption: CellInput | None = None,
        column_widths: Sequence[float] | None = None,
        identifier: str | None = None,
    ) -> None:
        self.headers = [coerce_cell(cell) for cell in headers]
        self.rows = [[coerce_cell(cell) for cell in row] for row in rows]
        self.caption = coerce_cell(caption) if caption is not None else None
        self.column_widths = list(column_widths) if column_widths is not None else None
        self.identifier = identifier

        if self.rows and any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("Each row must contain the same number of cells as the headers")
        if self.column_widths is not None and len(self.column_widths) != len(self.headers):
            raise ValueError("column_widths must match the number of headers")


@dataclass(slots=True)
class Figure(Block):
    """An image with an optional caption."""

    image_path: PathLike
    caption: Paragraph | None = None
    width_inches: float | None = None
    identifier: str | None = None

    def __post_init__(self) -> None:
        self.image_path = Path(self.image_path)
        if self.caption is not None and not isinstance(self.caption, Paragraph):
            self.caption = coerce_cell(self.caption)


@dataclass(slots=True, init=False)
class CitationSource:
    """A bibliography entry defined with Python data."""

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


@dataclass(slots=True)
class CitationReferenceEntry:
    """A numbered bibliography entry that was cited in the document."""

    number: int
    source: CitationSource


@dataclass(slots=True)
class HeadingEntry:
    """A heading included in the generated table of contents."""

    level: int
    title: list[Text]


@dataclass(slots=True)
class CitationLibrary:
    """Collection of bibliography entries addressable by citation key."""

    entries: dict[str, CitationSource] = field(default_factory=dict)

    def __init__(self, entries: Sequence[CitationSource] | None = None) -> None:
        self.entries = {}
        if entries is not None:
            for entry in entries:
                self.add(entry)

    def add(self, entry: CitationSource) -> None:
        if not entry.key:
            raise DocscriptorError("CitationSource.key is required when adding entries to a CitationLibrary")
        if entry.key in self.entries:
            raise DocscriptorError(f"Duplicate citation key: {entry.key!r}")
        self.entries[entry.key] = entry

    def resolve(self, key: str) -> CitationSource:
        if key not in self.entries:
            raise DocscriptorError(f"Unknown citation key: {key!r}")
        return self.entries[key]

    @classmethod
    def from_bibtex(cls, source: str) -> CitationLibrary:
        entries: list[CitationSource] = []
        for key, fields in _parse_bibtex_entries(source):
            authors = tuple(part.strip() for part in fields.get("author", "").split(" and ") if part.strip())
            entries.append(
                CitationSource(
                    title=fields.get("title", key),
                    key=key,
                    authors=authors,
                    organization=fields.get("organization") or fields.get("institution"),
                    publisher=fields.get("publisher") or fields.get("journal") or fields.get("booktitle") or fields.get("howpublished"),
                    year=fields.get("year"),
                    url=fields.get("url"),
                    note=fields.get("note"),
                )
            )
        return cls(entries)


@dataclass(slots=True)
class CaptionEntry:
    """A numbered captioned block entry."""

    number: int
    block: Table | Figure


@dataclass(slots=True)
class RenderIndex:
    """Numbering and lookup information derived from a document tree."""

    tables: list[CaptionEntry] = field(default_factory=list)
    figures: list[CaptionEntry] = field(default_factory=list)
    table_numbers: dict[int, int] = field(default_factory=dict)
    figure_numbers: dict[int, int] = field(default_factory=dict)
    citations: list[CitationReferenceEntry] = field(default_factory=list)
    citation_numbers: dict[str, int] = field(default_factory=dict)
    citation_source_numbers: dict[int, int] = field(default_factory=dict)
    headings: list[HeadingEntry] = field(default_factory=list)

    def table_number(self, table: Table) -> int | None:
        return self.table_numbers.get(id(table))

    def figure_number(self, figure: Figure) -> int | None:
        return self.figure_numbers.get(id(figure))

    def citation_number(self, target: CitationSource | str) -> int:
        if isinstance(target, CitationSource):
            if target.key is not None and target.key in self.citation_numbers:
                return self.citation_numbers[target.key]
            source_id = id(target)
            if source_id in self.citation_source_numbers:
                return self.citation_source_numbers[source_id]
            raise DocscriptorError(f"Unknown citation source: {target.title!r}")
        if target not in self.citation_numbers:
            raise DocscriptorError(f"Unknown citation key: {target!r}")
        return self.citation_numbers[target]


def build_render_index(document: Document) -> RenderIndex:
    """Scan a document tree and assign numbers to captioned figures and tables."""

    render_index = RenderIndex()
    _index_blocks(document.body.children, render_index, document.citations)
    return render_index


def _index_blocks(blocks: Sequence[Block], render_index: RenderIndex, citations: CitationLibrary) -> None:
    for block in blocks:
        if isinstance(block, Paragraph):
            _index_inlines(block.content, render_index, citations)
            continue
        if isinstance(block, (BulletList, NumberedList)):
            for item in block.items:
                _index_inlines(item.content, render_index, citations)
            continue
        if isinstance(block, Section):
            _index_inlines(block.title, render_index, citations)
            render_index.headings.append(HeadingEntry(level=block.level, title=block.title))
            _index_blocks(block.children, render_index, citations)
            continue
        if isinstance(block, (TableList, FigureList, ReferencesPage, TableOfContents)):
            if block.title is not None:
                _index_inlines(block.title, render_index, citations)
            continue
        if isinstance(block, Table):
            for header in block.headers:
                _index_inlines(header.content, render_index, citations)
            for row in block.rows:
                for cell in row:
                    _index_inlines(cell.content, render_index, citations)
            if block.caption is not None:
                _index_inlines(block.caption.content, render_index, citations)
                number = len(render_index.tables) + 1
                render_index.tables.append(CaptionEntry(number=number, block=block))
                render_index.table_numbers[id(block)] = number
            continue
        if isinstance(block, Figure):
            if block.caption is not None:
                _index_inlines(block.caption.content, render_index, citations)
                number = len(render_index.figures) + 1
                render_index.figures.append(CaptionEntry(number=number, block=block))
                render_index.figure_numbers[id(block)] = number
            continue


def _index_inlines(fragments: Sequence[Text], render_index: RenderIndex, citations: CitationLibrary) -> None:
    for fragment in fragments:
        if not isinstance(fragment, Citation):
            continue

        target = fragment.target
        if isinstance(target, CitationSource):
            if target.key is not None and target.key in render_index.citation_numbers:
                continue
            if id(target) in render_index.citation_source_numbers:
                continue
            source = target
        else:
            if target in render_index.citation_numbers:
                continue
            source = citations.resolve(target)

        number = len(render_index.citations) + 1
        render_index.citations.append(CitationReferenceEntry(number=number, source=source))
        render_index.citation_source_numbers[id(source)] = number
        if source.key is not None:
            render_index.citation_numbers[source.key] = number


def _coerce_citation_library(value: CitationLibrary | Sequence[CitationSource] | str | None) -> CitationLibrary:
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


@dataclass(slots=True, init=False)
class Document:
    """A renderable document."""

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
        self.citations = _coerce_citation_library(citations)

    def save_docx(self, path: PathLike) -> Path:
        """Render the document into a DOCX file and return the output path."""

        from docscriptor.renderers.docx import DocxRenderer

        return DocxRenderer().render(self, path)

    def save_pdf(self, path: PathLike) -> Path:
        """Render the document into a PDF file and return the output path."""

        from docscriptor.renderers.pdf import PdfRenderer

        return PdfRenderer().render(self, path)
