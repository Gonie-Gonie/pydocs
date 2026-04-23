"""Block-level document objects and recursive render dispatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence, TYPE_CHECKING

from docscriptor.equations import equation_plain_text
from docscriptor.inline import InlineInput, Text, coerce_inlines
from docscriptor.styles import BoxStyle, ListStyle, ParagraphStyle

if TYPE_CHECKING:
    from docscriptor.renderers.context import DocxRenderContext, PdfRenderContext


class Block:
    """Base class for block-level document objects."""

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        """Render the block into a DOCX container."""

        raise NotImplementedError

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the block into one or more PDF flowables."""

        raise NotImplementedError


@dataclass(slots=True, init=False)
class Paragraph(Block):
    """A paragraph built from inline fragments."""

    content: list[Text]
    style: ParagraphStyle

    def __init__(
        self,
        *content: InlineInput,
        style: ParagraphStyle | None = None,
    ) -> None:
        self.content = coerce_inlines(content)
        self.style = style or ParagraphStyle()

    def plain_text(self) -> str:
        """Return the paragraph content without styling metadata."""

        return "".join(fragment.plain_text() for fragment in self.content)

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_paragraph(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_paragraph(self, context)


ListInput = Paragraph | InlineInput


def coerce_list_item(value: ListInput) -> Paragraph:
    """Normalize a list item into a ``Paragraph`` instance."""

    if isinstance(value, Paragraph):
        return value
    return Paragraph(value)


@dataclass(slots=True, init=False)
class ListBlock(Block):
    """Shared implementation for bullet and ordered lists."""

    items: list[Paragraph]
    ordered: bool
    style: ListStyle | None

    def __init__(
        self,
        *items: ListInput,
        ordered: bool = False,
        style: ListStyle | None = None,
    ) -> None:
        self.items = [coerce_list_item(item) for item in items if item is not None]
        self.ordered = ordered
        self.style = style

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_list(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_list(self, context)


class BulletList(ListBlock):
    """An unordered list of paragraph items."""

    def __init__(self, *items: ListInput, style: ListStyle | None = None) -> None:
        super().__init__(*items, ordered=False, style=style)


class NumberedList(ListBlock):
    """An ordered list of paragraph items."""

    def __init__(self, *items: ListInput, style: ListStyle | None = None) -> None:
        super().__init__(*items, ordered=True, style=style)


@dataclass(slots=True)
class CodeBlock(Block):
    """A preformatted code snippet."""

    code: str
    language: str | None = None
    style: ParagraphStyle = field(
        default_factory=lambda: ParagraphStyle(alignment="left", space_after=12.0)
    )

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_code_block(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_code_block(self, context)


@dataclass(slots=True)
class Equation(Block):
    """A centered block equation written in lightweight LaTeX syntax."""

    expression: str
    style: ParagraphStyle = field(
        default_factory=lambda: ParagraphStyle(alignment="center", space_after=12.0)
    )

    def plain_text(self) -> str:
        """Return a readable plain-text equation approximation."""

        return equation_plain_text(self.expression)

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_equation(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_equation(self, context)


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


@dataclass(slots=True, init=False)
class TableOfContents(Block):
    """Generated outline of authored headings."""

    title: list[Text] | None

    def __init__(self, title: InlineInput | None = None) -> None:
        self.title = coerce_inlines((title,)) if title is not None else None

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


BlockInput = Block | str | Sequence["BlockInput"] | None


def coerce_blocks(values: Iterable[BlockInput]) -> list[Block]:
    """Normalize supported block inputs into block objects."""

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
    """Top-level block container used by ``Document``."""

    children: list[Block]

    def __init__(self, *children: BlockInput) -> None:
        self.children = coerce_blocks(children)

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        for child in self.children:
            child.render_to_docx(renderer, container, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        story: list[object] = []
        for child in self.children:
            story.extend(child.render_to_pdf(renderer, context))
        return story


@dataclass(slots=True, init=False)
class Box(Block):
    """Bordered container for grouped block content."""

    children: list[Block]
    title: list[Text] | None
    style: BoxStyle

    def __init__(
        self,
        *children: BlockInput,
        title: InlineInput | None = None,
        style: BoxStyle | None = None,
    ) -> None:
        self.children = coerce_blocks(children)
        self.title = coerce_inlines((title,)) if title is not None else None
        self.style = style or BoxStyle()

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.render_box(container, self, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        return renderer.render_box(self, context)


@dataclass(slots=True, init=False)
class Section(Block):
    """A titled section containing nested blocks."""

    title: list[Text]
    children: list[Block]
    level: int
    numbered: bool

    def __init__(
        self,
        title: InlineInput,
        *children: BlockInput,
        level: int = 2,
        numbered: bool = True,
    ) -> None:
        if level < 1:
            raise ValueError("Section level must be >= 1")
        self.title = coerce_inlines((title,))
        self.children = coerce_blocks(children)
        self.level = level
        self.numbered = numbered

    def plain_title(self) -> str:
        """Return the title without styling metadata."""

        return "".join(fragment.plain_text() for fragment in self.title)

    def render_to_docx(
        self,
        renderer: object,
        container: object,
        context: DocxRenderContext,
    ) -> None:
        renderer.add_heading(
            container,
            self.title,
            self.level,
            context,
            number_label=(
                context.render_index.heading_number(self)
                if self.numbered
                else None
            ),
            anchor=(
                context.render_index.heading_anchor(self)
                if self.numbered
                else None
            ),
        )
        for child in self.children:
            child.render_to_docx(renderer, container, context)

    def render_to_pdf(
        self,
        renderer: object,
        context: PdfRenderContext,
    ) -> list[object]:
        story = [renderer.make_section_heading(self, context)]
        for child in self.children:
            story.extend(child.render_to_pdf(renderer, context))
        return story


class Chapter(Section):
    """First-level document division."""

    def __init__(
        self,
        title: InlineInput,
        *children: BlockInput,
        numbered: bool = True,
    ) -> None:
        super().__init__(title, *children, level=1, numbered=numbered)


class Subsection(Section):
    """Third-level document division."""

    def __init__(
        self,
        title: InlineInput,
        *children: BlockInput,
        numbered: bool = True,
    ) -> None:
        super().__init__(title, *children, level=3, numbered=numbered)


class Subsubsection(Section):
    """Fourth-level document division."""

    def __init__(
        self,
        title: InlineInput,
        *children: BlockInput,
        numbered: bool = True,
    ) -> None:
        super().__init__(title, *children, level=4, numbered=numbered)


CellInput = Paragraph | InlineInput


def coerce_cell(value: CellInput) -> Paragraph:
    """Normalize table or figure caption content into a ``Paragraph``."""

    if isinstance(value, Paragraph):
        return value
    return Paragraph(value)
