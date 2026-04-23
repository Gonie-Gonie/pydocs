"""Public style objects and theme configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from docscriptor.core import format_counter_value, normalize_color, normalize_counter_format


@dataclass(slots=True)
class TextStyle:
    """Inline text styling overrides.

    Each field is optional so styles can be layered and merged.
    """

    font_name: str | None = None
    font_size: float | None = None
    color: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None

    def __post_init__(self) -> None:
        self.color = normalize_color(self.color)

    def merged(self, *others: TextStyle | None) -> TextStyle:
        """Return a new style with later values overriding earlier ones."""

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
            for field_name in (
                "font_name",
                "font_size",
                "color",
                "bold",
                "italic",
                "underline",
            ):
                value = getattr(other, field_name)
                if value is not None:
                    setattr(merged, field_name, value)
        return merged


@dataclass(slots=True)
class ParagraphStyle:
    """Block-level paragraph spacing and alignment settings."""

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
        self.formats = tuple(normalize_counter_format(value) for value in self.formats)
        if not self.formats:
            raise ValueError("HeadingNumbering.formats must not be empty")

    def format_label(self, counters: Sequence[int]) -> str | None:
        """Render a heading label such as ``1.2.3`` from nested counters."""

        if not self.enabled:
            return None

        pieces = [
            format_counter_value(value, self.formats[min(index, len(self.formats) - 1)])
            for index, value in enumerate(counters)
        ]
        return f"{self.prefix}{self.separator.join(pieces)}{self.suffix}"


@dataclass(slots=True)
class ListStyle:
    """Marker formatting for bullet and ordered lists."""

    marker_format: str = "decimal"
    bullet: str = "\u2022"
    prefix: str = ""
    suffix: str = "."
    start: int = 1
    indent: float = 0.25
    marker_gap: float = 0.1

    def __post_init__(self) -> None:
        self.marker_format = normalize_counter_format(self.marker_format)
        if self.start < 1:
            raise ValueError("ListStyle.start must be >= 1")
        if self.indent < 0:
            raise ValueError("ListStyle.indent must be >= 0")
        if self.marker_gap < 0:
            raise ValueError("ListStyle.marker_gap must be >= 0")

    def marker_for(self, index: int) -> str:
        """Return the rendered marker for a zero-based list item index."""

        if self.marker_format == "none":
            return ""

        marker_value = format_counter_value(
            index + self.start,
            self.marker_format,
            bullet=self.bullet,
        )
        return f"{self.prefix}{marker_value}{self.suffix}"


@dataclass(slots=True)
class BoxStyle:
    """Shared box styling for visually grouped content."""

    border_color: str = "B7C2D0"
    background_color: str = "F7FAFC"
    title_background_color: str | None = None
    border_width: float = 0.75
    padding: float = 6.0
    space_after: float = 12.0

    def __post_init__(self) -> None:
        self.border_color = normalize_color(self.border_color) or "B7C2D0"
        self.background_color = normalize_color(self.background_color) or "F7FAFC"
        self.title_background_color = normalize_color(self.title_background_color)
        if self.border_width < 0:
            raise ValueError("BoxStyle.border_width must be >= 0")
        if self.padding < 0:
            raise ValueError("BoxStyle.padding must be >= 0")
        if self.space_after < 0:
            raise ValueError("BoxStyle.space_after must be >= 0")


@dataclass(slots=True)
class TableStyle:
    """Renderer-neutral table styling options."""

    header_background_color: str = "E8EDF5"
    header_text_color: str = "000000"
    border_color: str = "B7C2D0"
    body_background_color: str | None = None
    alternate_row_background_color: str | None = None
    cell_padding: float = 5.0

    def __post_init__(self) -> None:
        self.header_background_color = normalize_color(self.header_background_color) or "E8EDF5"
        self.header_text_color = normalize_color(self.header_text_color) or "000000"
        self.border_color = normalize_color(self.border_color) or "B7C2D0"
        self.body_background_color = normalize_color(self.body_background_color)
        self.alternate_row_background_color = normalize_color(self.alternate_row_background_color)
        if self.cell_padding < 0:
            raise ValueError("TableStyle.cell_padding must be >= 0")


@dataclass(slots=True)
class Theme:
    """Document-wide renderer defaults.

    The theme controls typography, generated section titles, heading numbering,
    list marker defaults, and footer page numbering.
    """

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
    bullet_list_style: ListStyle = field(
        default_factory=lambda: ListStyle(marker_format="bullet", suffix="")
    )
    numbered_list_style: ListStyle = field(default_factory=ListStyle)

    def __post_init__(self) -> None:
        if self.page_number_alignment not in {"left", "center", "right"}:
            raise ValueError(
                f"Unsupported page number alignment: {self.page_number_alignment!r}"
            )
        if "{page}" not in self.page_number_format:
            raise ValueError("page_number_format must contain a '{page}' placeholder")

    def heading_size(self, level: int) -> float:
        """Return the configured font size for a heading level."""

        index = min(max(level - 1, 0), len(self.heading_sizes) - 1)
        return self.heading_sizes[index]

    def heading_emphasis(self, level: int) -> tuple[bool, bool]:
        """Return ``(bold, italic)`` emphasis for the given heading level."""

        emphasis = (
            (True, False),
            (True, False),
            (True, True),
            (False, True),
        )
        index = min(max(level - 1, 0), len(emphasis) - 1)
        return emphasis[index]

    def heading_alignment(self, level: int) -> str:
        """Return the alignment to use for the given heading level."""

        return "center" if level == 1 else "left"

    def format_page_number(self, page_number: int) -> str:
        """Render the footer page number string for a page."""

        return self.page_number_format.format(page=page_number)

    def format_heading_label(self, counters: Sequence[int]) -> str | None:
        """Render a heading numbering label for nested section counters."""

        return self.heading_numbering.format_label(counters)

    def list_style(self, *, ordered: bool) -> ListStyle:
        """Return the default style for bullet or ordered lists."""

        return self.numbered_list_style if ordered else self.bullet_list_style
