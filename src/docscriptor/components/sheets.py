"""Fixed-layout sheet components for short form-style documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TYPE_CHECKING

from docscriptor.components.base import Block
from docscriptor.components.inline import InlineInput, Text, coerce_inlines
from docscriptor.core import PathLike, normalize_color, normalize_length_unit

if TYPE_CHECKING:
    from docscriptor.renderers.context import DocxRenderContext, HtmlRenderContext, PdfRenderContext


SheetShapeKind = Literal["rect", "ellipse", "line"]
SheetImageFit = Literal["contain", "stretch"]


@dataclass(slots=True, init=False)
class TextBox:
    """Positioned text on a fixed-layout sheet.

    Coordinates are measured from the top-left corner of the sheet.
    """

    content: list[Text]
    x: float
    y: float
    width: float
    height: float
    align: str
    valign: str
    font_size: float | None
    z_index: int

    def __init__(
        self,
        *content: InlineInput,
        x: float,
        y: float,
        width: float,
        height: float,
        align: str = "left",
        valign: str = "top",
        font_size: float | None = None,
        z_index: int = 0,
    ) -> None:
        if align not in {"left", "center", "right"}:
            raise ValueError(f"Unsupported TextBox alignment: {align!r}")
        if valign not in {"top", "middle", "bottom"}:
            raise ValueError(f"Unsupported TextBox vertical alignment: {valign!r}")
        if width < 0 or height < 0:
            raise ValueError("TextBox width and height must be >= 0")
        self.content = coerce_inlines(content)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.align = align
        self.valign = valign
        self.font_size = font_size
        self.z_index = z_index

    def plain_text(self) -> str:
        """Return the textbox content without styling metadata."""

        return "".join(fragment.plain_text() for fragment in self.content)


@dataclass(slots=True, init=False)
class Shape:
    """A basic positioned shape for a fixed-layout sheet."""

    kind: SheetShapeKind
    x: float
    y: float
    width: float
    height: float
    stroke_color: str | None
    fill_color: str | None
    stroke_width: float
    z_index: int

    def __init__(
        self,
        kind: SheetShapeKind,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        stroke_color: str | None = "000000",
        fill_color: str | None = None,
        stroke_width: float = 1.0,
        z_index: int = 0,
    ) -> None:
        if kind not in {"rect", "ellipse", "line"}:
            raise ValueError(f"Unsupported shape kind: {kind!r}")
        if stroke_width < 0:
            raise ValueError("Shape stroke_width must be >= 0")
        self.kind = kind
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.stroke_color = normalize_color(stroke_color)
        self.fill_color = normalize_color(fill_color)
        self.stroke_width = stroke_width
        self.z_index = z_index

    @classmethod
    def rect(cls, *, x: float, y: float, width: float, height: float, **kwargs: object) -> Shape:
        return cls("rect", x=x, y=y, width=width, height=height, **kwargs)

    @classmethod
    def ellipse(cls, *, x: float, y: float, width: float, height: float, **kwargs: object) -> Shape:
        return cls("ellipse", x=x, y=y, width=width, height=height, **kwargs)

    @classmethod
    def line(cls, *, x: float, y: float, width: float, height: float, **kwargs: object) -> Shape:
        return cls("line", x=x, y=y, width=width, height=height, **kwargs)


@dataclass(slots=True, init=False)
class ImageBox:
    """A positioned image on a fixed-layout sheet."""

    image_source: object
    x: float
    y: float
    width: float
    height: float
    fit: SheetImageFit
    format: str
    dpi: int | None
    z_index: int

    def __init__(
        self,
        image_source: PathLike | object,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        fit: SheetImageFit = "contain",
        format: str = "png",
        dpi: int | None = 150,
        z_index: int = 0,
    ) -> None:
        if width < 0 or height < 0:
            raise ValueError("ImageBox width and height must be >= 0")
        if fit not in {"contain", "stretch"}:
            raise ValueError(f"Unsupported ImageBox fit: {fit!r}")
        self.image_source = (
            Path(image_source)
            if isinstance(image_source, (str, Path))
            else image_source
        )
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fit = fit
        self.format = format
        self.dpi = dpi
        self.z_index = z_index


@dataclass(slots=True, init=False)
class Sheet(Block):
    """A fixed-layout block for one-page forms such as certificates.

    A sheet is still part of the normal ``Document`` tree. It is intended for
    short, visually precise pages rather than long flowing prose.
    """

    items: list[TextBox | Shape | ImageBox]
    width: float | None
    height: float | None
    unit: str | None
    background_color: str
    border_color: str | None
    border_width: float
    page_break_after: bool

    def __init__(
        self,
        *items: TextBox | Shape | ImageBox,
        width: float | None = None,
        height: float | None = None,
        unit: str | None = None,
        background_color: str = "FFFFFF",
        border_color: str | None = None,
        border_width: float = 0.0,
        page_break_after: bool = False,
    ) -> None:
        if width is not None and width <= 0:
            raise ValueError("Sheet width must be > 0")
        if height is not None and height <= 0:
            raise ValueError("Sheet height must be > 0")
        if border_width < 0:
            raise ValueError("Sheet border_width must be >= 0")
        self.items = list(items)
        self.width = width
        self.height = height
        self.unit = normalize_length_unit(unit) if unit is not None else None
        self.background_color = normalize_color(background_color) or "FFFFFF"
        self.border_color = normalize_color(border_color)
        self.border_width = border_width
        self.page_break_after = page_break_after

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_sheet(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_sheet(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_sheet(self, context)


__all__ = ["ImageBox", "Shape", "Sheet", "TextBox"]
