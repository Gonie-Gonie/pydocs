"""Table and figure block objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TYPE_CHECKING

from docscriptor.blocks import Block, CellInput, Paragraph, coerce_cell
from docscriptor.core import PathLike, normalize_color
from docscriptor.styles import TableStyle

if TYPE_CHECKING:
    from docscriptor.renderers.context import DocxRenderContext, PdfRenderContext


@dataclass(slots=True, init=False)
class TableCell:
    """A single table cell with optional row or column spanning."""

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
        self.background_color = normalize_color(background_color)


TableCellInput = TableCell | CellInput


def coerce_table_cell(value: TableCellInput) -> TableCell:
    """Normalize supported cell inputs into a ``TableCell`` instance."""

    if isinstance(value, TableCell):
        return value
    return TableCell(value)


def _is_nested_table_input(values: Sequence[object]) -> bool:
    if not values:
        return False
    return all(
        isinstance(item, Sequence) and not isinstance(item, (str, Paragraph, TableCell))
        for item in values
    )


def _coerce_table_matrix(
    values: Sequence[TableCellInput] | Sequence[Sequence[TableCellInput]],
) -> list[list[TableCell]]:
    items = list(values)
    if _is_nested_table_input(items):
        return [
            [coerce_table_cell(cell) for cell in row]
            for row in items
        ]  # type: ignore[arg-type]
    return [[coerce_table_cell(cell) for cell in items]]  # type: ignore[arg-type]


def _is_dataframe_like(value: object) -> bool:
    return hasattr(value, "columns") and (
        hasattr(value, "itertuples") or hasattr(value, "to_numpy")
    )


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
    max_levels = (
        max(len(value) if isinstance(value, tuple) else 1 for value in raw_values)
        if raw_values
        else 1
    )
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
            if all(
                all(part == "" for part in column_values[offset][level + 1 :])
                for offset in range(column_index, column_index + colspan)
            ):
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
            body_rows.append(
                row_headers[row_index]
                + [TableCell("" if value is None else str(value)) for value in row_values]
            )
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
        header_rows[0] = [
            TableCell(name, rowspan=len(header_rows))
            for name in index_names
        ] + header_rows[0]
        return header_rows
    return [[TableCell(name) for name in index_names]]


@dataclass(slots=True)
class TablePlacement:
    """A positioned cell inside a rectangular table layout."""

    row: int
    column: int
    cell: TableCell
    header: bool
    body_row_index: int | None = None


@dataclass(slots=True)
class TableLayout:
    """Expanded rectangular table layout used by renderers."""

    row_count: int
    column_count: int
    header_row_count: int
    placements: list[TablePlacement]


def build_table_layout(
    header_rows: Sequence[Sequence[TableCell]],
    body_rows: Sequence[Sequence[TableCell]],
) -> TableLayout:
    """Expand spanned cells into positioned placements for renderer output."""

    all_rows = [(True, row, None) for row in header_rows] + [
        (False, row, body_row_index)
        for body_row_index, row in enumerate(body_rows)
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
        column_count = max(column_count, max(active_rowspans.keys(), default=-1) + 1)

    return TableLayout(
        row_count=len(all_rows),
        column_count=column_count,
        header_row_count=len(header_rows),
        placements=placements,
    )


@dataclass(slots=True, init=False)
class Table(Block):
    """A table supporting explicit spans and dataframe-like inputs."""

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
            self.header_rows = _dataframe_header_rows(
                dataframe,
                include_index=include_index,
            )
            self.rows = _dataframe_body_rows(dataframe, include_index=include_index)
        else:
            if rows is None:
                raise ValueError(
                    "rows is required unless the first argument is a dataframe-like object"
                )
            self.header_rows = _coerce_table_matrix(headers)  # type: ignore[arg-type]
            self.rows = [
                [coerce_table_cell(cell) for cell in row]
                for row in rows
            ]

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
        """Return the first header row for compatibility with older code."""

        return self.header_rows[0]

    def layout(self) -> TableLayout:
        """Return the renderer-facing table layout."""

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
        """Create a table directly from a dataframe-like object."""

        return cls(
            dataframe,
            caption=caption,
            column_widths=column_widths,
            identifier=identifier,
            style=style,
            include_index=include_index,
        )

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_table(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_table(self, context)


@dataclass(slots=True, init=False)
class Figure(Block):
    """An image block backed by a path or ``savefig()``-compatible object."""

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
        self.image_source = (
            Path(image_source)
            if isinstance(image_source, (str, Path))
            else image_source
        )
        self.caption = coerce_cell(caption) if caption is not None else None
        self.width_inches = width_inches
        self.identifier = identifier
        self.format = format
        self.dpi = dpi

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_figure(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_figure(self, context)
