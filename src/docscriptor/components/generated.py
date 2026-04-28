"""Generated page blocks and document summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from docscriptor.components.base import Block
from docscriptor.components.inline import InlineInput, Text, coerce_inlines

if TYPE_CHECKING:
    from docscriptor.renderers.context import DocxRenderContext, HtmlRenderContext, PdfRenderContext


@dataclass(slots=True)
class TocLevelStyle:
    """Optional display overrides for a table-of-contents level."""

    indent: float | None = None
    space_before: float | None = None
    space_after: float | None = None
    font_size_delta: float | None = None
    bold: bool | None = None
    italic: bool | None = None


@dataclass(slots=True, init=False)
class TableList(Block):
    """Generated list of captioned tables."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_table_list(self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_table_list(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_table_list(self, context)


@dataclass(slots=True, init=False)
class FigureList(Block):
    """Generated list of captioned figures."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_figure_list(self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_figure_list(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_figure_list(self, context)


@dataclass(slots=True, init=False)
class ReferencesPage(Block):
    """Generated reference list for cited bibliography entries."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_references_page(self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_references_page(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_references_page(self, context)


@dataclass(slots=True, init=False)
class CommentsPage(Block):
    """Generated page listing numbered inline comments."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_comments_page(self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_comments_page(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_comments_page(self, context)


@dataclass(slots=True, init=False)
class FootnotesPage(Block):
    """Generated page listing numbered portable footnotes."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_footnotes_page(self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_footnotes_page(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_footnotes_page(self, context)


@dataclass(slots=True, init=False)
class TableOfContents(Block):
    """Generated outline of authored headings."""

    title: list[Text] | None
    show_page_numbers: bool
    leader: str
    max_level: int | None
    level_styles: dict[int, TocLevelStyle]

    def __init__(
        self,
        title: InlineInput | None = None,
        *,
        show_page_numbers: bool = True,
        leader: str = ".",
        max_level: int | None = None,
        level_styles: dict[int, TocLevelStyle] | None = None,
    ) -> None:
        if max_level is not None and max_level < 1:
            raise ValueError("TableOfContents.max_level must be >= 1")
        self.title = coerce_inlines((title,)) if title is not None else None
        self.show_page_numbers = show_page_numbers
        self.leader = leader
        self.max_level = max_level
        self.level_styles = dict(level_styles or {})

    def includes_level(self, level: int) -> bool:
        return self.max_level is None or level <= self.max_level

    def style_for_level(self, level: int) -> TocLevelStyle:
        return self.level_styles.get(level, TocLevelStyle())

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_table_of_contents(self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_table_of_contents(self, context)

    def render_to_html(
        self,
        renderer: object,
        context: HtmlRenderContext,
    ) -> str:
        return renderer.render_table_of_contents(self, context)

__all__ = [
    "CommentsPage",
    "FigureList",
    "FootnotesPage",
    "ReferencesPage",
    "TableList",
    "TableOfContents",
    "TocLevelStyle",
]
