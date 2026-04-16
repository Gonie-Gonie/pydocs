"""Core document model for docscriptor."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
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


class Strong(Text):
    """Bold inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(bold=True).merged(style))


class Emphasis(Text):
    """Italic inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(italic=True).merged(style))


class Code(Text):
    """Monospace inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(font_name="Courier New").merged(style))


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

    def __init__(
        self,
        headers: Sequence[CellInput],
        rows: Sequence[Sequence[CellInput]],
        *,
        caption: CellInput | None = None,
        column_widths: Sequence[float] | None = None,
    ) -> None:
        self.headers = [coerce_cell(cell) for cell in headers]
        self.rows = [[coerce_cell(cell) for cell in row] for row in rows]
        self.caption = coerce_cell(caption) if caption is not None else None
        self.column_widths = list(column_widths) if column_widths is not None else None

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

    def __post_init__(self) -> None:
        self.image_path = Path(self.image_path)
        if self.caption is not None and not isinstance(self.caption, Paragraph):
            self.caption = coerce_cell(self.caption)


@dataclass(slots=True, init=False)
class Document:
    """A renderable document."""

    title: str
    body: Body
    author: str | None
    summary: str | None
    theme: Theme

    def __init__(
        self,
        title: str,
        *children: BlockInput,
        body: Body | None = None,
        author: str | None = None,
        summary: str | None = None,
        theme: Theme | None = None,
    ) -> None:
        if body is not None and children:
            raise ValueError("Pass either body=... or positional blocks, not both")

        self.title = title
        self.body = body if body is not None else Body(*children)
        self.author = author
        self.summary = summary
        self.theme = theme or Theme()

    def save_docx(self, path: PathLike) -> Path:
        """Render the document into a DOCX file and return the output path."""

        from docscriptor.renderers.docx import DocxRenderer

        return DocxRenderer().render(self, path)

    def save_pdf(self, path: PathLike) -> Path:
        """Render the document into a PDF file and return the output path."""

        from docscriptor.renderers.pdf import PdfRenderer

        return PdfRenderer().render(self, path)
