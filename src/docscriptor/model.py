"""Core document model for docscriptor."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable, Sequence

from docscriptor.equations import equation_plain_text


PathLike = str | Path


class DocscriptorError(Exception):
    """Raised when a document structure cannot be rendered."""


COUNTER_FORMATS = {
    "decimal",
    "lower-alpha",
    "upper-alpha",
    "lower-roman",
    "upper-roman",
    "bullet",
    "none",
}


def _normalize_color(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lstrip("#").upper()
    if len(normalized) != 6 or any(char not in "0123456789ABCDEF" for char in normalized):
        raise ValueError(f"Expected a 6-digit hex color, got: {value!r}")
    return normalized


def _normalize_counter_format(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in COUNTER_FORMATS:
        raise ValueError(f"Unsupported counter format: {value!r}")
    return normalized


def _alpha_counter(value: int) -> str:
    if value < 1:
        raise ValueError("Alphabetic counters require values >= 1")

    characters: list[str] = []
    number = value
    while number > 0:
        number -= 1
        characters.append(chr(ord("a") + (number % 26)))
        number //= 26
    return "".join(reversed(characters))


def _roman_counter(value: int) -> str:
    if value < 1:
        raise ValueError("Roman numeral counters require values >= 1")

    numerals = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    remaining = value
    parts: list[str] = []
    for numeral_value, glyph in numerals:
        while remaining >= numeral_value:
            parts.append(glyph)
            remaining -= numeral_value
    return "".join(parts)


def format_counter_value(value: int, counter_format: str, *, bullet: str = "•") -> str:
    """Format an integer using a supported numbering style."""

    normalized = _normalize_counter_format(counter_format)
    if normalized == "decimal":
        return str(value)
    if normalized == "lower-alpha":
        return _alpha_counter(value)
    if normalized == "upper-alpha":
        return _alpha_counter(value).upper()
    if normalized == "lower-roman":
        return _roman_counter(value).lower()
    if normalized == "upper-roman":
        return _roman_counter(value)
    if normalized == "bullet":
        return bullet
    return ""


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
class HeadingNumbering:
    """Configurable hierarchical numbering for authored headings."""

    enabled: bool = True
    formats: tuple[str, ...] = ("decimal", "decimal", "decimal", "decimal")
    separator: str = "."
    prefix: str = ""
    suffix: str = ""

    def __post_init__(self) -> None:
        self.formats = tuple(_normalize_counter_format(value) for value in self.formats)
        if not self.formats:
            raise ValueError("HeadingNumbering.formats must not be empty")

    def format_label(self, counters: Sequence[int]) -> str | None:
        if not self.enabled:
            return None

        pieces = [
            format_counter_value(value, self.formats[min(index, len(self.formats) - 1)])
            for index, value in enumerate(counters)
        ]
        return f"{self.prefix}{self.separator.join(pieces)}{self.suffix}"


@dataclass(slots=True)
class ListStyle:
    """Configurable marker formatting for bullet and ordered lists."""

    marker_format: str = "decimal"
    bullet: str = "•"
    prefix: str = ""
    suffix: str = "."
    start: int = 1
    indent: float = 0.25
    marker_gap: float = 0.1

    def __post_init__(self) -> None:
        self.marker_format = _normalize_counter_format(self.marker_format)
        if self.start < 1:
            raise ValueError("ListStyle.start must be >= 1")
        if self.indent < 0:
            raise ValueError("ListStyle.indent must be >= 0")
        if self.marker_gap < 0:
            raise ValueError("ListStyle.marker_gap must be >= 0")

    def marker_for(self, index: int) -> str:
        if self.marker_format == "none":
            return ""

        marker_value = format_counter_value(index + self.start, self.marker_format, bullet=self.bullet)
        return f"{self.prefix}{marker_value}{self.suffix}"


@dataclass(slots=True)
class BoxStyle:
    """Shared box styling used by DOCX and PDF renderers."""

    border_color: str = "B7C2D0"
    background_color: str = "F7FAFC"
    title_background_color: str | None = None
    border_width: float = 0.75
    padding: float = 6.0
    space_after: float = 12.0

    def __post_init__(self) -> None:
        self.border_color = _normalize_color(self.border_color) or "B7C2D0"
        self.background_color = _normalize_color(self.background_color) or "F7FAFC"
        self.title_background_color = _normalize_color(self.title_background_color)
        if self.border_width < 0:
            raise ValueError("BoxStyle.border_width must be >= 0")
        if self.padding < 0:
            raise ValueError("BoxStyle.padding must be >= 0")
        if self.space_after < 0:
            raise ValueError("BoxStyle.space_after must be >= 0")


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
    comments_title: str = "Comments"
    footnotes_title: str = "Footnotes"
    references_title: str = "References"
    contents_title: str = "Contents"
    generated_section_level: int = 2
    show_page_numbers: bool = False
    page_number_alignment: str = "center"
    page_number_format: str = "{page}"
    page_number_font_size: float = 9.0
    heading_numbering: HeadingNumbering = field(default_factory=HeadingNumbering)
    bullet_list_style: ListStyle = field(default_factory=lambda: ListStyle(marker_format="bullet", suffix=""))
    numbered_list_style: ListStyle = field(default_factory=ListStyle)

    def __post_init__(self) -> None:
        if self.page_number_alignment not in {"left", "center", "right"}:
            raise ValueError(f"Unsupported page number alignment: {self.page_number_alignment!r}")
        if "{page}" not in self.page_number_format:
            raise ValueError("page_number_format must contain a '{page}' placeholder")

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

    def format_page_number(self, page_number: int) -> str:
        return self.page_number_format.format(page=page_number)

    def format_heading_label(self, counters: Sequence[int]) -> str | None:
        return self.heading_numbering.format_label(counters)

    def list_style(self, *, ordered: bool) -> ListStyle:
        return self.numbered_list_style if ordered else self.bullet_list_style


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


class Comment(Text):
    """Inline text annotated with a numbered comment."""

    __slots__ = ("comment", "author", "initials")

    def __init__(
        self,
        value: str,
        *comment: InlineInput,
        author: str | None = None,
        initials: str | None = None,
        style: TextStyle | None = None,
    ) -> None:
        super().__init__(value=value, style=style or TextStyle())
        self.comment = coerce_inlines(comment)
        self.author = author
        self.initials = initials

    def plain_text(self) -> str:
        return f"{self.value}[?]"


def comment(
    value: str,
    *note: InlineInput,
    author: str | None = None,
    initials: str | None = None,
    style: TextStyle | None = None,
) -> Comment:
    """Create inline text with an attached numbered comment."""

    return Comment(value, *note, author=author, initials=initials, style=style)


class Footnote(Text):
    """Inline text annotated with a portable numbered footnote."""

    __slots__ = ("note",)

    def __init__(self, value: str, *note: InlineInput, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=style or TextStyle())
        self.note = coerce_inlines(note)

    def plain_text(self) -> str:
        return f"{self.value}[?]"


def footnote(value: str, *note: InlineInput, style: TextStyle | None = None) -> Footnote:
    """Create inline text with a numbered portable footnote."""

    return Footnote(value, *note, style=style)


class Math(Text):
    """Inline math fragment written in lightweight LaTeX syntax."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle().merged(style))

    def plain_text(self) -> str:
        return equation_plain_text(self.value)


def math(value: str, *, style: TextStyle | None = None) -> Math:
    """Create an inline math fragment from a LaTeX-like expression."""

    return Math(value, style=style)


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
    style: ListStyle | None

    def __init__(self, *items: ListInput, ordered: bool = False, style: ListStyle | None = None) -> None:
        self.items = [coerce_list_item(item) for item in items if item is not None]
        self.ordered = ordered
        self.style = style


class BulletList(_ListBlock):
    """An unordered list of paragraphs."""

    def __init__(self, *items: ListInput, style: ListStyle | None = None) -> None:
        super().__init__(*items, ordered=False, style=style)


class NumberedList(_ListBlock):
    """An ordered list of paragraphs."""

    def __init__(self, *items: ListInput, style: ListStyle | None = None) -> None:
        super().__init__(*items, ordered=True, style=style)


@dataclass(slots=True)
class CodeBlock(Block):
    """A block-level preformatted code snippet."""

    code: str
    language: str | None = None
    style: ParagraphStyle = field(default_factory=lambda: ParagraphStyle(space_after=12.0))


@dataclass(slots=True)
class Equation(Block):
    """A centered block equation written in lightweight LaTeX syntax."""

    expression: str
    style: ParagraphStyle = field(default_factory=lambda: ParagraphStyle(alignment="center", space_after=12.0))

    def plain_text(self) -> str:
        return equation_plain_text(self.expression)


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
class CommentsPage(Block):
    """Generated page for numbered comments encountered in the document."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None


@dataclass(slots=True, init=False)
class FootnotesPage(Block):
    """Generated page for numbered footnotes encountered in the document."""

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
class Box(Block):
    """A bordered container for arbitrary authored blocks."""

    children: list[Block]
    title: list[Text] | None
    style: BoxStyle

    def __init__(self, *children: BlockInput, title: InlineInput | None = None, style: BoxStyle | None = None) -> None:
        self.children = coerce_blocks(children)
        self.title = coerce_inlines((title,)) if title is not None else None
        self.style = style or BoxStyle()


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
class TableCell:
    """A table cell with optional row and column spanning."""

    content: Paragraph
    colspan: int
    rowspan: int
    background_color: str | None

    def __init__(
        self,
        value: CellInput,
        *,
        colspan: int = 1,
        rowspan: int = 1,
        background_color: str | None = None,
    ) -> None:
        if colspan < 1:
            raise ValueError("TableCell.colspan must be >= 1")
        if rowspan < 1:
            raise ValueError("TableCell.rowspan must be >= 1")
        self.content = coerce_cell(value)
        self.colspan = colspan
        self.rowspan = rowspan
        self.background_color = _normalize_color(background_color)


@dataclass(slots=True)
class TableStyle:
    """Shared table styling used by DOCX and PDF renderers."""

    header_background_color: str = "E8EDF5"
    header_text_color: str = "000000"
    border_color: str = "B7C2D0"
    body_background_color: str | None = None
    alternate_row_background_color: str | None = None
    cell_padding: float = 5.0

    def __post_init__(self) -> None:
        self.header_background_color = _normalize_color(self.header_background_color) or "E8EDF5"
        self.header_text_color = _normalize_color(self.header_text_color) or "000000"
        self.border_color = _normalize_color(self.border_color) or "B7C2D0"
        self.body_background_color = _normalize_color(self.body_background_color)
        self.alternate_row_background_color = _normalize_color(self.alternate_row_background_color)
        if self.cell_padding < 0:
            raise ValueError("TableStyle.cell_padding must be >= 0")


TableCellInput = TableCell | CellInput


def coerce_table_cell(value: TableCellInput) -> TableCell:
    if isinstance(value, TableCell):
        return value
    return TableCell(value)


def _is_nested_table_input(values: Sequence[object]) -> bool:
    if not values:
        return False
    if not all(isinstance(item, Sequence) and not isinstance(item, (str, Paragraph, TableCell, Text)) for item in values):
        return False
    return any(not all(isinstance(part, Text) for part in item) for item in values)


def _coerce_table_matrix(values: Sequence[TableCellInput] | Sequence[Sequence[TableCellInput]]) -> list[list[TableCell]]:
    items = list(values)
    if _is_nested_table_input(items):
        return [[coerce_table_cell(cell) for cell in row] for row in items]  # type: ignore[arg-type]
    return [[coerce_table_cell(cell) for cell in items]]  # type: ignore[arg-type]


def _is_dataframe_like(value: object) -> bool:
    return hasattr(value, "columns") and (hasattr(value, "itertuples") or hasattr(value, "to_numpy"))


def _axis_labels(values: object) -> list[object]:
    if hasattr(values, "tolist"):
        return list(values.tolist())
    return list(values)


def _axis_names(values: object) -> tuple[str, ...]:
    names = getattr(values, "names", None)
    if names is not None:
        return tuple("" if name is None else str(name) for name in names)
    name = getattr(values, "name", None)
    return ("" if name is None else str(name),)


def _normalize_axis_values(values: object) -> list[tuple[str, ...]]:
    raw_values = _axis_labels(values)
    normalized: list[tuple[str, ...]] = []
    max_levels = max((len(value) if isinstance(value, tuple) else 1) for value in raw_values) if raw_values else 1
    for value in raw_values:
        if isinstance(value, tuple):
            parts = tuple("" if part is None else str(part) for part in value)
        else:
            parts = ("" if value is None else str(value),)
        normalized.append(parts + ("",) * (max_levels - len(parts)))
    return normalized


def _build_column_header_rows(column_values: list[tuple[str, ...]]) -> list[list[TableCell]]:
    if not column_values:
        return [[TableCell("")]]

    level_count = len(column_values[0])
    header_rows: list[list[TableCell]] = []
    for level in range(level_count):
        row: list[TableCell] = []
        column_index = 0
        while column_index < len(column_values):
            label = column_values[column_index][level]
            prefix = column_values[column_index][:level]
            if label == "":
                column_index += 1
                continue
            colspan = 1
            while (
                column_index + colspan < len(column_values)
                and column_values[column_index + colspan][level] == label
                and column_values[column_index + colspan][:level] == prefix
            ):
                colspan += 1
            rowspan = 1
            if all(all(part == "" for part in column_values[offset][level + 1 :]) for offset in range(column_index, column_index + colspan)):
                rowspan = level_count - level
            row.append(TableCell(label, colspan=colspan, rowspan=rowspan))
            column_index += colspan
        header_rows.append(row)
    return header_rows


def _build_row_header_cells(index_values: list[tuple[str, ...]]) -> list[list[TableCell]]:
    if not index_values:
        return []

    row_headers: list[list[TableCell]] = [[] for _ in index_values]
    level_count = len(index_values[0])
    for level in range(level_count):
        row_index = 0
        while row_index < len(index_values):
            label = index_values[row_index][level]
            prefix = index_values[row_index][:level]
            rowspan = 1
            while (
                row_index + rowspan < len(index_values)
                and index_values[row_index + rowspan][level] == label
                and index_values[row_index + rowspan][:level] == prefix
            ):
                rowspan += 1
            row_headers[row_index].append(TableCell(label, rowspan=rowspan))
            row_index += rowspan
    return row_headers


def _dataframe_body_rows(dataframe: object, *, include_index: bool) -> list[list[TableCell]]:
    data_rows: list[tuple[object, ...]]
    if hasattr(dataframe, "itertuples"):
        data_rows = [tuple(row) for row in dataframe.itertuples(index=False, name=None)]
    else:
        matrix = dataframe.to_numpy().tolist()  # type: ignore[call-arg]
        data_rows = [tuple(row) for row in matrix]

    body_rows: list[list[TableCell]] = []
    if include_index:
        index_values = _normalize_axis_values(dataframe.index)
        row_headers = _build_row_header_cells(index_values)
        for row_index, row_values in enumerate(data_rows):
            header_cells = row_headers[row_index]
            body_rows.append(header_cells + [TableCell("" if value is None else str(value)) for value in row_values])
        return body_rows

    for row_values in data_rows:
        body_rows.append([TableCell("" if value is None else str(value)) for value in row_values])
    return body_rows


def _dataframe_header_rows(dataframe: object, *, include_index: bool) -> list[list[TableCell]]:
    column_values = _normalize_axis_values(dataframe.columns)
    header_rows = _build_column_header_rows(column_values)
    if not include_index:
        return header_rows

    index_names = _axis_names(dataframe.index)
    if header_rows:
        header_rows[0] = [TableCell(name, rowspan=len(header_rows)) for name in index_names] + header_rows[0]
        return header_rows
    return [[TableCell(name) for name in index_names]]


@dataclass(slots=True)
class TablePlacement:
    """A positioned table cell inside a rectangular layout."""

    row: int
    column: int
    cell: TableCell
    header: bool
    body_row_index: int | None = None


@dataclass(slots=True)
class TableLayout:
    """Expanded rectangular grid for renderer-specific table output."""

    row_count: int
    column_count: int
    header_row_count: int
    placements: list[TablePlacement]


def build_table_layout(header_rows: Sequence[Sequence[TableCell]], body_rows: Sequence[Sequence[TableCell]]) -> TableLayout:
    all_rows = [(True, row, None) for row in header_rows] + [
        (False, row, body_row_index) for body_row_index, row in enumerate(body_rows)
    ]
    active_rowspans: dict[int, int] = {}
    placements: list[TablePlacement] = []
    column_count = 0

    for row_index, (is_header, row_cells, body_row_index) in enumerate(all_rows):
        pending_rowspans = {
            column: remaining - 1
            for column, remaining in active_rowspans.items()
            if remaining > 1
        }
        rowspans_from_current: dict[int, int] = {}
        column_index = 0
        for cell in row_cells:
            while active_rowspans.get(column_index, 0) > 0:
                column_index += 1
            placements.append(
                TablePlacement(
                    row=row_index,
                    column=column_index,
                    cell=cell,
                    header=is_header,
                    body_row_index=body_row_index,
                )
            )
            for offset in range(cell.colspan):
                column = column_index + offset
                if active_rowspans.get(column, 0) > 0:
                    raise ValueError("Table cell spans overlap")
                if cell.rowspan > 1:
                    rowspans_from_current[column] = cell.rowspan - 1
            column_index += cell.colspan

        column_count = max(
            column_count,
            column_index,
            (max(active_rowspans.keys(), default=-1) + 1) if active_rowspans else 0,
        )
        active_rowspans = pending_rowspans | rowspans_from_current

    if active_rowspans:
        last_column = max(active_rowspans.keys(), default=-1) + 1
        column_count = max(column_count, last_column)

    return TableLayout(
        row_count=len(all_rows),
        column_count=column_count,
        header_row_count=len(header_rows),
        placements=placements,
    )


@dataclass(slots=True, init=False)
class Table(Block):
    """A table supporting spans, styling, and dataframe-like inputs."""

    header_rows: list[list[TableCell]]
    rows: list[list[TableCell]]
    caption: Paragraph | None
    column_widths: list[float] | None
    identifier: str | None
    style: TableStyle
    include_index: bool

    def __init__(
        self,
        headers: Sequence[TableCellInput] | Sequence[Sequence[TableCellInput]] | object,
        rows: Sequence[Sequence[TableCellInput]] | None = None,
        *,
        caption: CellInput | None = None,
        column_widths: Sequence[float] | None = None,
        identifier: str | None = None,
        style: TableStyle | None = None,
        include_index: bool = False,
    ) -> None:
        if rows is None and _is_dataframe_like(headers):
            dataframe = headers
            self.header_rows = _dataframe_header_rows(dataframe, include_index=include_index)
            self.rows = _dataframe_body_rows(dataframe, include_index=include_index)
        else:
            if rows is None:
                raise ValueError("rows is required unless the first argument is a dataframe-like object")
            self.header_rows = _coerce_table_matrix(headers)  # type: ignore[arg-type]
            self.rows = [[coerce_table_cell(cell) for cell in row] for row in rows]

        self.caption = coerce_cell(caption) if caption is not None else None
        self.column_widths = list(column_widths) if column_widths is not None else None
        self.identifier = identifier
        self.style = style or TableStyle()
        self.include_index = include_index

        layout = self.layout()
        if self.column_widths is not None and len(self.column_widths) != layout.column_count:
            raise ValueError("column_widths must match the expanded number of table columns")

    @property
    def headers(self) -> list[TableCell]:
        return self.header_rows[0]

    def layout(self) -> TableLayout:
        return build_table_layout(self.header_rows, self.rows)

    @classmethod
    def from_dataframe(
        cls,
        dataframe: object,
        *,
        caption: CellInput | None = None,
        column_widths: Sequence[float] | None = None,
        identifier: str | None = None,
        style: TableStyle | None = None,
        include_index: bool = False,
    ) -> Table:
        return cls(
            dataframe,
            caption=caption,
            column_widths=column_widths,
            identifier=identifier,
            style=style,
            include_index=include_index,
        )


@dataclass(slots=True, init=False)
class Figure(Block):
    """An image or figure-like object with an optional caption."""

    image_source: object
    caption: Paragraph | None
    width_inches: float | None
    identifier: str | None
    format: str
    dpi: int | None

    def __init__(
        self,
        image_source: PathLike | object,
        caption: CellInput | None = None,
        width_inches: float | None = None,
        identifier: str | None = None,
        *,
        format: str = "png",
        dpi: int | None = 150,
    ) -> None:
        self.image_source = Path(image_source) if isinstance(image_source, (str, Path)) else image_source
        self.caption = coerce_cell(caption) if caption is not None else None
        self.width_inches = width_inches
        self.identifier = identifier
        self.format = format
        self.dpi = dpi


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
class CommentReferenceEntry:
    """A numbered comment encountered in the document tree."""

    number: int
    comment: Comment


@dataclass(slots=True)
class FootnoteReferenceEntry:
    """A numbered footnote encountered in the document tree."""

    number: int
    footnote: Footnote


@dataclass(slots=True)
class HeadingEntry:
    """A heading included in the generated table of contents."""

    level: int
    title: list[Text]
    number: str | None = None


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
    comments: list[CommentReferenceEntry] = field(default_factory=list)
    comment_numbers: dict[int, int] = field(default_factory=dict)
    footnotes: list[FootnoteReferenceEntry] = field(default_factory=list)
    footnote_numbers: dict[int, int] = field(default_factory=dict)
    headings: list[HeadingEntry] = field(default_factory=list)
    heading_numbers: dict[int, str] = field(default_factory=dict)

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

    def comment_number(self, target: Comment) -> int:
        if id(target) not in self.comment_numbers:
            raise DocscriptorError(f"Unknown comment target: {target.value!r}")
        return self.comment_numbers[id(target)]

    def footnote_number(self, target: Footnote) -> int:
        if id(target) not in self.footnote_numbers:
            raise DocscriptorError(f"Unknown footnote target: {target.value!r}")
        return self.footnote_numbers[id(target)]

    def heading_number(self, target: Section) -> str | None:
        return self.heading_numbers.get(id(target))


def build_render_index(document: Document) -> RenderIndex:
    """Scan a document tree and assign numbers to captioned figures and tables."""

    render_index = RenderIndex()
    _index_blocks(
        document.body.children,
        render_index,
        document.citations,
        document.theme,
        heading_counters=[],
    )
    return render_index


def _advance_heading_counters(counters: list[int], level: int) -> list[int]:
    while len(counters) < level:
        counters.append(0)
    for index in range(max(level - 1, 0)):
        if counters[index] == 0:
            counters[index] = 1
    counters[level - 1] += 1
    del counters[level:]
    return counters


def _index_blocks(
    blocks: Sequence[Block],
    render_index: RenderIndex,
    citations: CitationLibrary,
    theme: Theme,
    *,
    heading_counters: list[int],
) -> None:
    for block in blocks:
        if isinstance(block, Paragraph):
            _index_inlines(block.content, render_index, citations)
            continue
        if isinstance(block, (BulletList, NumberedList)):
            for item in block.items:
                _index_inlines(item.content, render_index, citations)
            continue
        if isinstance(block, Equation):
            continue
        if isinstance(block, Box):
            if block.title is not None:
                _index_inlines(block.title, render_index, citations)
            _index_blocks(
                block.children,
                render_index,
                citations,
                theme,
                heading_counters=list(heading_counters),
            )
            continue
        if isinstance(block, Section):
            _index_inlines(block.title, render_index, citations)
            current_counters = _advance_heading_counters(list(heading_counters), block.level)
            number_label = theme.format_heading_label(current_counters[: block.level])
            render_index.headings.append(HeadingEntry(level=block.level, title=block.title, number=number_label))
            if number_label is not None:
                render_index.heading_numbers[id(block)] = number_label
            _index_blocks(
                block.children,
                render_index,
                citations,
                theme,
                heading_counters=current_counters,
            )
            continue
        if isinstance(block, (TableList, FigureList, ReferencesPage, CommentsPage, FootnotesPage, TableOfContents)):
            if block.title is not None:
                _index_inlines(block.title, render_index, citations)
            continue
        if isinstance(block, Table):
            for header_row in block.header_rows:
                for header in header_row:
                    _index_inlines(header.content.content, render_index, citations)
            for row in block.rows:
                for cell in row:
                    _index_inlines(cell.content.content, render_index, citations)
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
        if isinstance(fragment, Comment):
            _index_inlines(fragment.comment, render_index, citations)
            if id(fragment) in render_index.comment_numbers:
                continue
            number = len(render_index.comments) + 1
            render_index.comments.append(CommentReferenceEntry(number=number, comment=fragment))
            render_index.comment_numbers[id(fragment)] = number
            continue
        if isinstance(fragment, Footnote):
            _index_inlines(fragment.note, render_index, citations)
            if id(fragment) in render_index.footnote_numbers:
                continue
            number = len(render_index.footnotes) + 1
            render_index.footnotes.append(FootnoteReferenceEntry(number=number, footnote=fragment))
            render_index.footnote_numbers[id(fragment)] = number
            continue
        if isinstance(fragment, Citation):
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
