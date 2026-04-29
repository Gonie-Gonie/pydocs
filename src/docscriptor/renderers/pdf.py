"""PDF renderer."""

from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle as RLParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak as RLPageBreak,
    Paragraph as RLParagraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table as RLTable,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents as RLTableOfContents

from docscriptor.components.blocks import (
    Box,
    BulletList,
    CodeBlock,
    Equation,
    NumberedList,
    PageBreak as DocscriptorPageBreak,
    Paragraph,
    Section,
)
from docscriptor.components.generated import (
    CommentsPage,
    FigureList,
    FootnotesPage,
    ReferencesPage,
    TableList,
    TableOfContents,
    TocLevelStyle,
)
from docscriptor.components.inline import (
    _BlockReference,
    Citation,
    Comment,
    Footnote,
    Hyperlink,
    Math,
    Text,
)
from docscriptor.components.media import Figure, Table, build_table_layout
from docscriptor.components.people import AuthorTitleLine
from docscriptor.components.sheets import ImageBox, Shape, Sheet, TextBox
from docscriptor.document import Document
from docscriptor.components.equations import SUBSCRIPT, SUPERSCRIPT, parse_latex_segments
from docscriptor.core import DocscriptorError, PathLike, length_to_inches
from docscriptor.layout.indexing import RenderIndex, build_render_index
from docscriptor.layout.theme import ParagraphStyle, Theme
from docscriptor.renderers.context import PdfRenderContext


ALIGNMENTS = {
    "left": TA_LEFT,
    "center": TA_CENTER,
    "right": TA_RIGHT,
    "justify": TA_JUSTIFY,
}

FLOWABLE_ALIGNMENTS = {
    "left": "LEFT",
    "center": "CENTER",
    "right": "RIGHT",
}

PDF_FONT_VARIANTS = {
    "Courier": {
        (False, False): "Courier",
        (True, False): "Courier-Bold",
        (False, True): "Courier-Oblique",
        (True, True): "Courier-BoldOblique",
    },
    "Helvetica": {
        (False, False): "Helvetica",
        (True, False): "Helvetica-Bold",
        (False, True): "Helvetica-Oblique",
        (True, True): "Helvetica-BoldOblique",
    },
    "Times-Roman": {
        (False, False): "Times-Roman",
        (True, False): "Times-Bold",
        (False, True): "Times-Italic",
        (True, True): "Times-BoldItalic",
    },
}

FONT_FAMILY_ALIASES = {
    "times new roman": "Times-Roman",
    "times": "Times-Roman",
    "times-roman": "Times-Roman",
    "courier new": "Courier",
    "courier": "Courier",
    "cambria math": "Times-Roman",
    "helvetica": "Helvetica",
    "arial": "Helvetica",
}

SYSTEM_FONT_VARIANTS = {
    "Times New Roman": {
        (False, False): ["C:/Windows/Fonts/times.ttf"],
        (True, False): ["C:/Windows/Fonts/timesbd.ttf"],
        (False, True): ["C:/Windows/Fonts/timesi.ttf"],
        (True, True): ["C:/Windows/Fonts/timesbi.ttf"],
    },
    "Courier New": {
        (False, False): ["C:/Windows/Fonts/cour.ttf"],
        (True, False): ["C:/Windows/Fonts/courbd.ttf"],
        (False, True): ["C:/Windows/Fonts/couri.ttf"],
        (True, True): ["C:/Windows/Fonts/courbi.ttf"],
    },
    "Arial": {
        (False, False): ["C:/Windows/Fonts/arial.ttf"],
        (True, False): ["C:/Windows/Fonts/arialbd.ttf"],
        (False, True): ["C:/Windows/Fonts/ariali.ttf"],
        (True, True): ["C:/Windows/Fonts/arialbi.ttf"],
    },
}


class PageNumberTransition(Flowable):
    """Invisible flowable that marks the beginning of a new page-numbering mode."""

    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        return (0, 0)

    def draw(self) -> None:
        return None


class FilteredTableOfContents(RLTableOfContents):
    """ReportLab TOC flowable with optional heading-level filtering."""

    def __init__(self, *, max_level: int | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.max_level = max_level

    def notify(self, kind: str, stuff: object) -> None:
        if kind == self._notifyKind and self.max_level is not None:
            level = stuff[0]  # type: ignore[index]
            if level + 1 > self.max_level:
                return
        super().notify(kind, stuff)


class SheetFlowable(Flowable):
    """ReportLab flowable that draws a fixed-layout sheet."""

    def __init__(
        self,
        sheet: Sheet,
        renderer: "PdfRenderer",
        context: PdfRenderContext,
    ) -> None:
        super().__init__()
        self.sheet = sheet
        self.renderer = renderer
        self.context = context
        self.width = renderer._sheet_width(sheet, context) * inch
        self.height = renderer._sheet_height(sheet, context) * inch

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        return (self.width, self.height)

    def draw(self) -> None:
        canvas = self.canv
        sheet = self.sheet
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(f"#{sheet.background_color}"))
        canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        if sheet.border_color is not None and sheet.border_width > 0:
            canvas.setStrokeColor(colors.HexColor(f"#{sheet.border_color}"))
            canvas.setLineWidth(sheet.border_width)
            canvas.rect(0, 0, self.width, self.height, fill=0, stroke=1)
        for item in self._items():
            if isinstance(item, TextBox):
                self._draw_text_box(item)
            elif isinstance(item, ImageBox):
                self._draw_image_box(item)
            else:
                self._draw_shape(item)
        canvas.restoreState()

    def _items(self) -> list[TextBox | Shape | ImageBox]:
        return [
            item
            for _, item in sorted(
                enumerate(self.sheet.items),
                key=lambda indexed: (indexed[1].z_index, indexed[0]),
            )
        ]

    def _length(self, value: float) -> float:
        return length_to_inches(value, self.sheet.unit or self.context.unit) * inch

    def _draw_text_box(self, item: TextBox) -> None:
        font_size = item.font_size or self.context.theme.body_font_size
        style = RLParagraphStyle(
            "SheetTextBox",
            fontName=self.renderer._resolve_font(self.context.theme.body_font_name, False, False),
            fontSize=font_size,
            leading=font_size * 1.22,
            alignment=ALIGNMENTS[item.align],
            textColor=colors.black,
        )
        paragraph = RLParagraph(
            self.renderer._inline_markup(
                item.content,
                self.context.theme,
                self.context.render_index,
                base_font_name=style.fontName,
                base_size=font_size,
            ),
            style,
        )
        x = self._length(item.x)
        y_top = self._length(item.y)
        width = self._length(item.width)
        height = self._length(item.height)
        _, paragraph_height = paragraph.wrap(width, height)
        if item.valign == "middle":
            y = self.height - y_top - ((height + paragraph_height) / 2)
        elif item.valign == "bottom":
            y = self.height - y_top - height
        else:
            y = self.height - y_top - paragraph_height
        paragraph.drawOn(self.canv, x, y)

    def _draw_shape(self, item: Shape) -> None:
        canvas = self.canv
        x = self._length(item.x)
        y_top = self._length(item.y)
        width = self._length(item.width)
        height = self._length(item.height)
        y = self.height - y_top - height
        if item.stroke_color is not None and item.stroke_width > 0:
            canvas.setStrokeColor(colors.HexColor(f"#{item.stroke_color}"))
            canvas.setLineWidth(item.stroke_width)
        if item.fill_color is not None:
            canvas.setFillColor(colors.HexColor(f"#{item.fill_color}"))
        fill = 1 if item.fill_color is not None else 0
        stroke = 1 if item.stroke_color is not None and item.stroke_width > 0 else 0
        if item.kind == "rect":
            canvas.rect(x, y, width, height, fill=fill, stroke=stroke)
        elif item.kind == "ellipse":
            canvas.ellipse(x, y, x + width, y + height, fill=fill, stroke=stroke)
        else:
            canvas.line(x, self.height - y_top, x + width, self.height - y_top - height)

    def _draw_image_box(self, item: ImageBox) -> None:
        x = self._length(item.x)
        y_top = self._length(item.y)
        width = self._length(item.width)
        height = self._length(item.height)
        y = self.height - y_top - height
        preserve_aspect_ratio = item.fit == "contain"
        self.canv.drawImage(
            self.renderer._image_box_source(item),
            x,
            y,
            width=width,
            height=height,
            preserveAspectRatio=preserve_aspect_ratio,
            anchor="c",
            mask="auto",
        )


class DocscriptorPdfTemplate(SimpleDocTemplate):
    """SimpleDocTemplate with page-number mode transitions."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.main_matter_start_page: int | None = None

    def afterFlowable(self, flowable: Flowable) -> None:
        if isinstance(flowable, PageNumberTransition) and flowable.mode == "main":
            self.main_matter_start_page = self.page + 1
            return
        toc_entry = getattr(flowable, "_docscriptor_toc_entry", None)
        if toc_entry is not None:
            level, text, key = toc_entry
            self.notify("TOCEntry", (level, text, self.page, key))


class PdfRenderer:
    """Render docscriptor documents into PDF files."""

    def __init__(self) -> None:
        self._registered_system_fonts: dict[tuple[str, bool, bool], str] = {}

    def render(self, document: Document, output_path: PathLike) -> Path:
        """Render a docscriptor document to a PDF file."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        pdf = DocscriptorPdfTemplate(
            str(path),
            pagesize=(
                document.settings.page_width_in_inches() * inch,
                document.settings.page_height_in_inches() * inch,
            ),
            title=document.title,
            author=document.author,
            leftMargin=document.settings.page_margins.left_in_inches(document.settings.unit) * inch,
            rightMargin=document.settings.page_margins.right_in_inches(document.settings.unit) * inch,
            topMargin=document.settings.page_margins.top_in_inches(document.settings.unit) * inch,
            bottomMargin=document.settings.page_margins.bottom_in_inches(document.settings.unit) * inch,
        )
        story: list[object] = []
        styles = getSampleStyleSheet()
        render_index = build_render_index(document)
        context = PdfRenderContext(
            theme=document.theme,
            render_index=render_index,
            settings=document.settings,
            unit=document.settings.unit,
            styles=styles,
        )

        front_children, main_children = document.split_top_level_children()
        has_front_matter = document.cover_page or bool(front_children)

        story.extend(self._render_title_matter(document, context))
        if document.cover_page and front_children:
            story.append(RLPageBreak())

        story.extend(self._render_top_level_children(front_children, context))
        if has_front_matter and main_children:
            story.append(PageNumberTransition("main"))
            if story and not isinstance(story[-2] if len(story) > 1 else None, RLPageBreak):
                story.append(RLPageBreak())
            story.extend(self._render_top_level_children(main_children, context))
        elif not has_front_matter:
            story.extend(self._render_top_level_children(main_children, context))

        if self._should_auto_render_footnotes_page(document, render_index):
            story.extend(self.render_footnotes_page(FootnotesPage(), context))

        page_callback = self._page_callback(
            document.theme,
            has_front_matter=has_front_matter,
        )
        if self._story_has_indexing_flowable(story):
            pdf.multiBuild(story, onFirstPage=page_callback, onLaterPages=page_callback)
        elif document.theme.show_page_numbers or document.theme.page_background_color != "FFFFFF":
            pdf.build(story, onFirstPage=page_callback, onLaterPages=page_callback)
        else:
            pdf.build(story)
        return path

    def make_section_heading(
        self,
        block: Section,
        context: PdfRenderContext,
    ) -> RLParagraph:
        """Build the PDF flowable used for a section heading."""

        theme = context.theme
        styles = context.styles
        render_index = context.render_index
        bold, italic = theme.heading_emphasis(block.level)
        title_style = RLParagraphStyle(
            f"Heading{block.level}",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(block.level),
            leading=theme.heading_size(block.level) * 1.2,
            spaceBefore=18 if block.level == 1 else 12,
            spaceAfter=10 if block.level == 1 else 6,
            alignment=ALIGNMENTS[theme.heading_alignment(block.level)],
            textColor=colors.black,
        )
        paragraph = RLParagraph(
            self._anchor_markup(render_index.heading_anchor(block))
            + self._inline_markup(
                self._heading_fragments(
                    block.title,
                    render_index.heading_number(block),
                ),
                theme,
                render_index,
                base_font_name=title_style.fontName,
                base_size=title_style.fontSize,
                base_bold=bold,
                base_italic=italic,
            ),
            title_style,
        )
        paragraph._docscriptor_toc_entry = (
            block.level - 1,
            self._flatten_fragments(
                self._heading_fragments(block.title, render_index.heading_number(block)),
                theme,
                render_index,
            ),
            render_index.heading_anchor(block),
        )
        return paragraph

    def render_paragraph(
        self,
        block: Paragraph,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a paragraph block into PDF flowables."""

        paragraph_style = self._paragraph_style(
            block.style,
            context.theme,
            context.styles["BodyText"],
        )
        return [
            RLParagraph(
                self._inline_markup(
                    block.content,
                    context.theme,
                    context.render_index,
                    base_font_name=paragraph_style.fontName,
                    base_size=paragraph_style.fontSize,
                ),
                paragraph_style,
            )
        ]

    def render_list(
        self,
        block: BulletList | NumberedList,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a list block into PDF flowables."""

        return self._render_list(
            block,
            context.theme,
            context.styles,
            context.render_index,
        )

    def render_code_block(
        self,
        block: CodeBlock,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a code block into PDF flowables."""

        return self._render_code_block(block, context.theme, context.styles)

    def render_equation(
        self,
        block: Equation,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a block equation into PDF flowables."""

        return self._render_equation(block, context.theme, context.styles)

    def render_page_break(
        self,
        block: DocscriptorPageBreak,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render an explicit page break into PDF flowables."""

        return [RLPageBreak()]

    def render_box(
        self,
        block: Box,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a box and its child blocks into PDF flowables."""

        return self._render_box(
            block,
            context.theme,
            context.styles,
            context.render_index,
            context.settings,
            context.unit,
        )

    def render_sheet(
        self,
        block: Sheet,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a fixed-layout sheet into PDF flowables."""

        story: list[object] = [SheetFlowable(block, self, context)]
        if block.page_break_after:
            story.append(RLPageBreak())
        return story

    def render_table(
        self,
        block: Table,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a table block into PDF flowables."""

        return self._render_table(
            block,
            context.theme,
            context.styles,
            context.render_index,
            context.unit,
        )

    def render_figure(
        self,
        block: Figure,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render a figure block into PDF flowables."""

        return self._render_figure(
            block,
            context.theme,
            context.styles,
            context.render_index,
            context.unit,
        )

    def render_table_list(
        self,
        block: TableList,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the generated list of tables into PDF flowables."""

        return self._render_caption_list(
            block.title,
            context.render_index.tables,
            context.theme,
            context.styles,
            context.render_index,
            context.theme.list_of_tables_title,
            context.theme.table_label,
        )

    def render_figure_list(
        self,
        block: FigureList,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the generated list of figures into PDF flowables."""

        return self._render_caption_list(
            block.title,
            context.render_index.figures,
            context.theme,
            context.styles,
            context.render_index,
            context.theme.list_of_figures_title,
            context.theme.figure_label,
        )

    def render_comments_page(
        self,
        block: CommentsPage,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the generated comments page into PDF flowables."""

        return self._render_comments_page(
            block.title,
            context.theme,
            context.styles,
            context.render_index,
        )

    def render_footnotes_page(
        self,
        block: FootnotesPage,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the generated footnotes page into PDF flowables."""

        return self._render_footnotes_page(
            block.title,
            context.theme,
            context.styles,
            context.render_index,
        )

    def render_references_page(
        self,
        block: ReferencesPage,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the generated references page into PDF flowables."""

        return self._render_references_page(
            block.title,
            context.theme,
            context.styles,
            context.render_index,
        )

    def render_table_of_contents(
        self,
        block: TableOfContents,
        context: PdfRenderContext,
    ) -> list[object]:
        """Render the generated table of contents into PDF flowables."""

        return self._render_table_of_contents(
            block,
            context,
        )

    def _render_block(
        self,
        block: object,
        context: PdfRenderContext,
    ) -> list[object]:
        """Delegate block rendering back to the block instance itself."""

        return block.render_to_pdf(self, context)

    def _render_top_level_children(
        self,
        children: list[object],
        context: PdfRenderContext,
    ) -> list[object]:
        story: list[object] = []
        for index, child in enumerate(children):
            if self._is_paginated_generated_page(child) and context.theme.generated_page_breaks:
                if story and not isinstance(story[-1], RLPageBreak):
                    story.append(RLPageBreak())
                story.extend(child.render_to_pdf(self, context))
                if index < len(children) - 1:
                    story.append(RLPageBreak())
                continue
            story.extend(child.render_to_pdf(self, context))
        return story

    def _render_title_matter(
        self,
        document: Document,
        context: PdfRenderContext,
    ) -> list[object]:
        theme = context.theme
        styles = context.styles
        story: list[object] = [
            self._title_paragraph(
                [Text(document.title)],
                theme,
                styles,
                style_name="DocscriptorTitle",
                font_size=theme.title_font_size,
                alignment=theme.title_alignment,
                bold=True,
                space_after=18,
            )
        ]
        if document.subtitle is not None:
            story.append(
                self._title_paragraph(
                    document.subtitle,
                    theme,
                    styles,
                    style_name="DocscriptorSubtitle",
                    font_size=max(theme.body_font_size + 1, 12),
                    alignment=theme.subtitle_alignment,
                    italic=True,
                    space_after=12,
                )
            )
        for line, is_last_for_author in document.settings.iter_author_title_lines():
            story.append(
                self._title_paragraph(
                    list(line.fragments),
                    theme,
                    styles,
                    style_name=f"DocscriptorAuthor{line.kind.title()}",
                    font_size=self._title_line_font_size(line, theme),
                    alignment=self._title_line_alignment(line, theme),
                    italic=line.kind == "affiliation",
                    space_after=12 if is_last_for_author else (4 if line.kind == "name" else 3),
                )
            )
        return story

    def _title_line_alignment(self, line: AuthorTitleLine, theme: Theme) -> str:
        if line.kind == "name":
            return theme.author_alignment
        if line.kind == "affiliation":
            return theme.affiliation_alignment
        return theme.author_detail_alignment

    def _title_line_font_size(self, line: AuthorTitleLine, theme: Theme) -> float:
        if line.kind == "name":
            return theme.body_font_size
        if line.kind == "affiliation":
            return max(theme.body_font_size - 0.5, 9)
        return max(theme.body_font_size - 1, 9)

    def _title_paragraph(
        self,
        fragments: list[Text],
        theme: Theme,
        styles: object,
        *,
        style_name: str,
        font_size: float,
        alignment: str,
        bold: bool = False,
        italic: bool = False,
        space_after: float = 0,
    ) -> RLParagraph:
        paragraph_style = RLParagraphStyle(
            style_name,
            parent=styles["BodyText"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=font_size,
            leading=font_size * 1.2,
            alignment=ALIGNMENTS[alignment],
            spaceAfter=space_after,
            textColor=colors.black,
        )
        return RLParagraph(
            self._inline_markup(
                fragments,
                theme,
                RenderIndex(),
                base_font_name=paragraph_style.fontName,
                base_size=paragraph_style.fontSize,
                base_bold=bold,
                base_italic=italic,
            ),
            paragraph_style,
        )

    def _is_paginated_generated_page(self, block: object) -> bool:
        return isinstance(block, (TableList, FigureList, TableOfContents))

    def _should_auto_render_footnotes_page(
        self,
        document: Document,
        render_index: RenderIndex,
    ) -> bool:
        return (
            document.theme.auto_footnotes_page
            and bool(render_index.footnotes)
            and not any(isinstance(child, FootnotesPage) for child in document.body.children)
        )

    def _story_has_indexing_flowable(self, story: list[object]) -> bool:
        return any(getattr(flowable, "isIndexing", lambda: False)() for flowable in story)

    def _sheet_width(self, sheet: Sheet, context: PdfRenderContext) -> float:
        if sheet.width is None:
            return context.settings.page_width_in_inches()
        return length_to_inches(sheet.width, sheet.unit or context.unit)

    def _sheet_height(self, sheet: Sheet, context: PdfRenderContext) -> float:
        if sheet.height is None:
            return context.settings.page_height_in_inches()
        return length_to_inches(sheet.height, sheet.unit or context.unit)

    def _paragraph_style(self, style: ParagraphStyle, theme: Theme, base_style: RLParagraphStyle) -> RLParagraphStyle:
        return RLParagraphStyle(
            f"Paragraph{style.alignment}{style.space_after}{style.leading}",
            parent=base_style,
            fontName=self._resolve_font(theme.body_font_name, False, False),
            fontSize=theme.body_font_size,
            leading=style.leading or theme.body_font_size * 1.35,
            spaceAfter=style.space_after or 0,
            alignment=ALIGNMENTS[style.alignment],
            textColor=colors.black,
        )

    def _assert_box_child_supported(self, child: object) -> None:
        if isinstance(
            child,
            (
                CommentsPage,
                FootnotesPage,
                ReferencesPage,
                TableOfContents,
                TableList,
                FigureList,
            ),
        ):
            raise DocscriptorError(
                f"{type(child).__name__} cannot be rendered inside a Box"
            )

    def _render_table(self, block: Table, theme: Theme, styles: object, render_index: RenderIndex, unit: str) -> list[object]:
        body_style = self._paragraph_style(ParagraphStyle(space_after=0), theme, styles["BodyText"])
        header_style = RLParagraphStyle(
            "TableHeader",
            parent=body_style,
            fontName=self._resolve_font(theme.body_font_name, True, False),
            textColor=colors.HexColor(f"#{block.style.header_text_color}"),
        )
        layout = build_table_layout(block.header_rows, block.rows)
        table_rows: list[list[object]] = [["" for _ in range(layout.column_count)] for _ in range(layout.row_count)]
        style_commands: list[tuple[str, tuple[int, int], tuple[int, int], object]] = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(f"#{block.style.border_color}")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), block.style.cell_padding),
            ("RIGHTPADDING", (0, 0), (-1, -1), block.style.cell_padding),
            ("TOPPADDING", (0, 0), (-1, -1), block.style.cell_padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), block.style.cell_padding),
        ]
        for placement in layout.placements:
            paragraph_style = header_style if placement.header else body_style
            table_rows[placement.row][placement.column] = RLParagraph(
                self._inline_markup(
                    placement.cell.content.content,
                    theme,
                    render_index,
                    base_font_name=paragraph_style.fontName,
                    base_size=paragraph_style.fontSize,
                    base_bold=placement.header,
                    base_italic=False,
                ),
                paragraph_style,
            )
            if placement.cell.colspan > 1 or placement.cell.rowspan > 1:
                style_commands.append(
                    (
                        "SPAN",
                        (placement.column, placement.row),
                        (
                            placement.column + placement.cell.colspan - 1,
                            placement.row + placement.cell.rowspan - 1,
                        ),
                    )
                )
            if placement.header:
                style_commands.append(
                    (
                        "BACKGROUND",
                        (placement.column, placement.row),
                        (
                            placement.column + placement.cell.colspan - 1,
                            placement.row + placement.cell.rowspan - 1,
                        ),
                        colors.HexColor(f"#{block.style.header_background_color}"),
                    )
                )
            else:
                background_color = placement.cell.background_color
                if background_color is None and block.style.alternate_row_background_color is not None and placement.body_row_index is not None and placement.body_row_index % 2 == 1:
                    background_color = block.style.alternate_row_background_color
                if background_color is None:
                    background_color = block.style.body_background_color
                if background_color is not None:
                    style_commands.append(
                        (
                            "BACKGROUND",
                            (placement.column, placement.row),
                            (
                                placement.column + placement.cell.colspan - 1,
                                placement.row + placement.cell.rowspan - 1,
                            ),
                            colors.HexColor(f"#{background_color}"),
                        )
                    )

        resolved_widths = block.column_widths_in_inches(unit)
        column_widths = [width * inch for width in resolved_widths] if resolved_widths is not None else None
        table = RLTable(
            table_rows,
            colWidths=column_widths,
            hAlign=FLOWABLE_ALIGNMENTS[theme.table_alignment],
        )
        table.setStyle(TableStyle(style_commands))

        story: list[object] = []
        if block.caption is not None and theme.table_caption_position == "above":
            caption_style = RLParagraphStyle(
                "TableCaption",
                parent=body_style,
                fontSize=theme.caption_size(),
                alignment=ALIGNMENTS[theme.caption_alignment],
                spaceBefore=0,
                spaceAfter=6,
            )
            story.append(
                RLParagraph(
                    self._anchor_markup(render_index.table_anchor(block))
                    + self._inline_markup(
                        self._caption_fragments(theme.table_label, render_index.table_number(block), block.caption),
                        theme,
                        render_index,
                        base_font_name=caption_style.fontName,
                        base_size=caption_style.fontSize,
                    ),
                    caption_style,
                )
            )
        story.append(table)
        if block.caption is not None and theme.table_caption_position == "below":
            caption_style = RLParagraphStyle(
                "TableCaption",
                parent=body_style,
                fontSize=theme.caption_size(),
                alignment=ALIGNMENTS[theme.caption_alignment],
                spaceBefore=6,
                spaceAfter=12,
            )
            story.append(
                RLParagraph(
                    self._anchor_markup(render_index.table_anchor(block))
                    + self._inline_markup(
                        self._caption_fragments(
                            theme.table_label,
                            render_index.table_number(block),
                            block.caption,
                        ),
                        theme,
                        render_index,
                        base_font_name=caption_style.fontName,
                        base_size=caption_style.fontSize,
                    ),
                    caption_style,
                )
            )
        else:
            story.append(Spacer(1, 12))
        if layout.row_count <= 12:
            return [KeepTogether(story)]
        return story

    def _render_list(self, block: BulletList | NumberedList, theme: Theme, styles: object, render_index: RenderIndex) -> list[object]:
        item_style = self._paragraph_style(ParagraphStyle(space_after=3), theme, styles["BodyText"])
        marker_style = RLParagraphStyle(
            "ListMarker",
            parent=item_style,
            alignment=TA_RIGHT,
            spaceAfter=3,
        )
        list_style = block.style or theme.list_style(ordered=isinstance(block, NumberedList))
        marker_width = max(list_style.indent * inch, 0.35 * inch)
        rows: list[list[object]] = []
        for index, item in enumerate(block.items):
            marker = list_style.marker_for(index)
            marker_markup = escape(marker) if marker else "&nbsp;"
            marker_paragraph = RLParagraph(marker_markup, marker_style)
            content_paragraph = RLParagraph(
                self._inline_markup(
                    item.content,
                    theme,
                    render_index,
                    base_font_name=item_style.fontName,
                    base_size=item_style.fontSize,
                ),
                item_style,
            )
            rows.append([marker_paragraph, content_paragraph])
        table = RLTable(rows, colWidths=[marker_width, None], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (1, 0), (1, -1), max(list_style.marker_gap * inch, 4)),
                ]
            )
        )
        return [table, Spacer(1, 8)]

    def _render_box(self, block: Box, theme: Theme, styles: object, render_index: RenderIndex, settings: object, unit: str) -> list[object]:
        body_style = self._paragraph_style(ParagraphStyle(space_after=0), theme, styles["BodyText"])
        rows: list[list[object]] = []
        row_styles: list[tuple[str, tuple[int, int], tuple[int, int], object]] = []
        if block.title is not None:
            title_style = RLParagraphStyle(
                "BoxTitle",
                parent=body_style,
                fontName=self._resolve_font(theme.body_font_name, True, False),
                spaceAfter=6,
            )
            rows.append(
                [
                    RLParagraph(
                        self._inline_markup(
                            block.title,
                            theme,
                            render_index,
                            base_font_name=title_style.fontName,
                            base_size=title_style.fontSize,
                            base_bold=True,
                            base_italic=False,
                        ),
                        title_style,
                    )
                ]
            )
            if block.style.title_background_color is not None:
                row_styles.append(
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
                        colors.HexColor(f"#{block.style.title_background_color}"),
                    )
                )
        for child in block.children:
            self._assert_box_child_supported(child)
            context = PdfRenderContext(
                theme=theme,
                render_index=render_index,
                settings=settings,
                unit=unit,
                styles=styles,
            )
            for flowable in self._render_block(child, context):
                if isinstance(flowable, KeepTogether):
                    rows.extend([[nested]] for nested in flowable._content)
                    continue
                rows.append([flowable])
        if not rows:
            rows.append([Spacer(1, 1)])

        table = RLTable(
            rows,
            hAlign=FLOWABLE_ALIGNMENTS[theme.box_alignment],
            repeatRows=0,
        )
        style_commands: list[tuple[str, tuple[int, int], tuple[int, int], object]] = [
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(f"#{block.style.background_color}")),
            ("BOX", (0, 0), (-1, -1), block.style.border_width, colors.HexColor(f"#{block.style.border_color}")),
            ("LEFTPADDING", (0, 0), (-1, -1), block.style.padding),
            ("RIGHTPADDING", (0, 0), (-1, -1), block.style.padding),
            ("TOPPADDING", (0, 0), (-1, -1), block.style.padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), block.style.padding),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        style_commands.extend(row_styles)
        table.setStyle(TableStyle(style_commands))
        return [table, Spacer(1, block.style.space_after)]

    def _render_code_block(self, block: CodeBlock, theme: Theme, styles: object) -> list[object]:
        code_style = RLParagraphStyle(
            "CodeBlock",
            parent=styles["Code"],
            fontName=self._resolve_font(theme.monospace_font_name, False, False),
            fontSize=max(theme.body_font_size - 1, 8),
            leading=max(theme.body_font_size - 1, 8) * 1.35,
            leftIndent=12,
            rightIndent=6,
            spaceBefore=6,
            spaceAfter=block.style.space_after or 0,
            borderPadding=8,
            borderWidth=0.75,
            borderColor=colors.HexColor("#D8E0EB"),
            backColor=colors.HexColor("#F5F7FA"),
        )

        elements: list[object] = []
        if block.language:
            label_style = RLParagraphStyle(
                "CodeBlockLabel",
                parent=styles["BodyText"],
                fontName=self._resolve_font(theme.monospace_font_name, True, False),
                fontSize=theme.caption_size(),
                alignment=TA_LEFT,
                spaceAfter=2,
            )
            elements.append(RLParagraph(escape(block.language.upper()), label_style))

        elements.append(Preformatted(block.code, code_style))
        return [KeepTogether(elements)]

    def _render_equation(self, block: Equation, theme: Theme, styles: object) -> list[object]:
        equation_style = RLParagraphStyle(
            "EquationBlock",
            parent=styles["BodyText"],
            fontName=self._resolve_font(theme.body_font_name, False, False),
            fontSize=max(theme.body_font_size + 1, 12),
            leading=max(theme.body_font_size + 1, 12) * 1.3,
            alignment=ALIGNMENTS[block.style.alignment],
            spaceAfter=block.style.space_after or 0,
            textColor=colors.black,
        )
        return [
            RLParagraph(
                self._math_markup(
                    Math(block.expression),
                    theme,
                    base_font_name=equation_style.fontName,
                    base_size=equation_style.fontSize,
                ),
                equation_style,
            )
        ]

    def _render_figure(self, block: Figure, theme: Theme, styles: object, render_index: RenderIndex, unit: str) -> list[object]:
        image = RLImage(self._figure_image_source(block))
        image.hAlign = FLOWABLE_ALIGNMENTS[theme.figure_alignment]
        resolved_width = block.width_in_inches(unit)
        resolved_height = block.height_in_inches(unit)
        if resolved_width is not None and resolved_height is not None:
            image.drawWidth = resolved_width * inch
            image.drawHeight = resolved_height * inch
        elif resolved_width is not None:
            target_width = resolved_width * inch
            scale = target_width / image.drawWidth
            image.drawWidth = target_width
            image.drawHeight = image.drawHeight * scale
        elif resolved_height is not None:
            target_height = resolved_height * inch
            scale = target_height / image.drawHeight
            image.drawHeight = target_height
            image.drawWidth = image.drawWidth * scale

        body_style = self._paragraph_style(ParagraphStyle(space_after=0), theme, styles["BodyText"])
        elements: list[object] = [image]
        if block.caption is not None and theme.figure_caption_position == "above":
            caption_style = RLParagraphStyle(
                "FigureCaption",
                parent=body_style,
                fontSize=theme.caption_size(),
                alignment=ALIGNMENTS[theme.caption_alignment],
                spaceBefore=0,
                spaceAfter=6,
            )
            elements = [
                RLParagraph(
                    self._anchor_markup(render_index.figure_anchor(block))
                    + self._inline_markup(
                        self._caption_fragments(theme.figure_label, render_index.figure_number(block), block.caption),
                        theme,
                        render_index,
                        base_font_name=caption_style.fontName,
                        base_size=caption_style.fontSize,
                    ),
                    caption_style,
                )
            ] + elements
        if block.caption is not None and theme.figure_caption_position == "below":
            caption_style = RLParagraphStyle(
                "FigureCaption",
                parent=body_style,
                fontSize=theme.caption_size(),
                alignment=ALIGNMENTS[theme.caption_alignment],
                spaceBefore=6,
                spaceAfter=12,
            )
            elements.append(
                RLParagraph(
                    self._anchor_markup(render_index.figure_anchor(block))
                    + self._inline_markup(
                        self._caption_fragments(theme.figure_label, render_index.figure_number(block), block.caption),
                        theme,
                        render_index,
                        base_font_name=caption_style.fontName,
                        base_size=caption_style.fontSize,
                    ),
                    caption_style,
                )
            )
        else:
            elements.append(Spacer(1, 12))
        return [KeepTogether(elements)]

    def _figure_image_source(self, block: Figure) -> str | BytesIO:
        source = block.image_source
        if isinstance(source, Path):
            return str(source)
        if hasattr(source, "savefig"):
            buffer = BytesIO()
            save_kwargs: dict[str, object] = {
                "format": block.format,
            }
            if block.dpi is not None:
                save_kwargs["dpi"] = block.dpi
            source.savefig(buffer, **save_kwargs)
            buffer.seek(0)
            return buffer
        raise TypeError(f"Unsupported figure source for PDF rendering: {type(source)!r}")

    def _image_box_source(self, image_box: ImageBox) -> str | ImageReader:
        source = image_box.image_source
        if isinstance(source, Path):
            return str(source)
        if hasattr(source, "savefig"):
            buffer = BytesIO()
            save_kwargs: dict[str, object] = {"format": image_box.format}
            if image_box.dpi is not None:
                save_kwargs["dpi"] = image_box.dpi
            source.savefig(buffer, **save_kwargs)
            buffer.seek(0)
            return ImageReader(buffer)
        raise TypeError(f"Unsupported image source for PDF sheet rendering: {type(source)!r}")

    def _inline_markup(
        self,
        fragments: list[Text],
        theme: Theme,
        render_index: RenderIndex,
        *,
        base_font_name: str | None = None,
        base_size: float | None = None,
        base_bold: bool = False,
        base_italic: bool = False,
    ) -> str:
        parts = [
            self._fragment_markup(
                fragment,
                theme,
                render_index,
                base_font_name=base_font_name,
                base_size=base_size,
                base_bold=base_bold,
                base_italic=base_italic,
            )
            for fragment in fragments
        ]
        return "".join(parts) or "&nbsp;"

    def _heading_fragments(self, title: list[Text], number_label: str | None) -> list[Text]:
        if not number_label:
            return title
        return [Text(f"{number_label} ")] + title

    def _fragment_markup(
        self,
        fragment: Text,
        theme: Theme,
        render_index: RenderIndex,
        *,
        base_font_name: str | None,
        base_size: float | None,
        base_bold: bool,
        base_italic: bool,
    ) -> str:
        if isinstance(fragment, Hyperlink):
            return self._link_markup(
                fragment.target,
                self._inline_markup(
                    fragment.label,
                    theme,
                    render_index,
                    base_font_name=base_font_name,
                    base_size=base_size,
                    base_bold=base_bold,
                    base_italic=base_italic,
                ),
                internal=fragment.internal,
            )
        if isinstance(fragment, _BlockReference):
            return self._link_markup(
                self._block_reference_anchor(fragment.target, render_index),
                self._styled_text_markup(
                    self._resolve_block_reference(fragment.target, theme, render_index),
                    fragment,
                    theme,
                    base_font_name=base_font_name,
                    base_size=base_size,
                    base_bold=base_bold,
                    base_italic=base_italic,
                ),
                internal=True,
            )
        if isinstance(fragment, Citation):
            return self._link_markup(
                render_index.citation_anchor(fragment.target),
                self._styled_text_markup(
                    f"[{render_index.citation_number(fragment.target)}]",
                    fragment,
                    theme,
                    base_font_name=base_font_name,
                    base_size=base_size,
                    base_bold=base_bold,
                    base_italic=base_italic,
                ),
                internal=True,
            )
        if isinstance(fragment, Comment):
            visible = self._styled_text_markup(
                fragment.value,
                fragment,
                theme,
                base_font_name=base_font_name,
                base_size=base_size,
                base_bold=base_bold,
                base_italic=base_italic,
            )
            return f"{visible}<super>{escape(self._comment_marker(fragment, render_index))}</super>"
        if isinstance(fragment, Footnote):
            visible = self._styled_text_markup(
                fragment.value,
                fragment,
                theme,
                base_font_name=base_font_name,
                base_size=base_size,
                base_bold=base_bold,
                base_italic=base_italic,
            )
            return f"{visible}<super>{escape(self._footnote_marker(fragment, render_index))}</super>"
        if isinstance(fragment, Math):
            return self._math_markup(
                fragment,
                theme,
                base_font_name=base_font_name,
                base_size=base_size,
                base_bold=base_bold,
                base_italic=base_italic,
            )
        return self._styled_text_markup(
            self._resolve_fragment_text(fragment, theme, render_index),
            fragment,
            theme,
            base_font_name=base_font_name,
            base_size=base_size,
            base_bold=base_bold,
            base_italic=base_italic,
        )

    def _styled_text_markup(
        self,
        text_value: str,
        fragment: Text,
        theme: Theme,
        *,
        base_font_name: str | None,
        base_size: float | None,
        base_bold: bool,
        base_italic: bool,
    ) -> str:
        text = escape(text_value).replace("\n", "<br/>")
        bold = base_bold if fragment.style.bold is None else fragment.style.bold
        italic = base_italic if fragment.style.italic is None else fragment.style.italic
        font_name = self._resolve_font(fragment.style.font_name or theme.body_font_name, bold, italic)
        size = fragment.style.font_size or base_size or theme.body_font_size

        font_attrs: list[str] = []
        if base_font_name is None or font_name != base_font_name:
            font_attrs.append(f'face="{font_name}"')
        if base_size is None or size != base_size:
            font_attrs.append(f'size="{size}"')
        if fragment.style.color is not None:
            font_attrs.append(f'color="#{fragment.style.color}"')
        wrapped = text if not font_attrs else f"<font {' '.join(font_attrs)}>{text}</font>"
        if fragment.style.underline:
            wrapped = f"<u>{wrapped}</u>"
        return wrapped

    def _math_markup(
        self,
        fragment: Math,
        theme: Theme,
        *,
        base_font_name: str | None,
        base_size: float | None,
        base_bold: bool = False,
        base_italic: bool = False,
    ) -> str:
        parts: list[str] = []
        for segment in parse_latex_segments(fragment.value):
            piece = self._styled_text_markup(
                segment.text,
                fragment,
                theme,
                base_font_name=base_font_name,
                base_size=base_size,
                base_bold=base_bold,
                base_italic=base_italic,
            )
            if segment.vertical_align == SUPERSCRIPT:
                piece = f"<super>{piece}</super>"
            elif segment.vertical_align == SUBSCRIPT:
                piece = f"<sub>{piece}</sub>"
            parts.append(piece)
        return "".join(parts) or "&nbsp;"

    def _resolve_font(self, font_name: str, bold: bool, italic: bool) -> str:
        system_font = self._register_system_font(font_name, bold, italic)
        if system_font is not None:
            return system_font
        aliased_font_name = FONT_FAMILY_ALIASES.get(font_name.lower(), font_name)
        font_name = aliased_font_name
        if font_name in PDF_FONT_VARIANTS:
            return PDF_FONT_VARIANTS[font_name][(bold, italic)]
        if font_name in pdfmetrics.getRegisteredFontNames():
            return font_name
        fallback = "Courier" if "Courier" in font_name else "Times-Roman" if "Times" in font_name else "Helvetica"
        return PDF_FONT_VARIANTS[fallback][(bold, italic)]

    def _register_system_font(self, font_name: str, bold: bool, italic: bool) -> str | None:
        key = (font_name, bold, italic)
        if key in self._registered_system_fonts:
            return self._registered_system_fonts[key]

        for candidate_name, variants in SYSTEM_FONT_VARIANTS.items():
            if candidate_name.lower() != font_name.lower():
                continue
            for font_path in variants[(bold, italic)]:
                if not Path(font_path).exists():
                    continue
                registered_name = f"{candidate_name}-{int(bold)}-{int(italic)}"
                if registered_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(registered_name, font_path))
                self._registered_system_fonts[key] = registered_name
                return registered_name
        return None

    def _resolve_fragment_text(self, fragment: Text, theme: Theme, render_index: RenderIndex) -> str:
        if isinstance(fragment, _BlockReference):
            return self._resolve_block_reference(fragment.target, theme, render_index)
        if isinstance(fragment, Citation):
            return f"[{render_index.citation_number(fragment.target)}]"
        if isinstance(fragment, Hyperlink):
            return fragment.plain_text()
        if isinstance(fragment, Comment):
            return fragment.value
        if isinstance(fragment, Footnote):
            return fragment.value
        if isinstance(fragment, Math):
            return fragment.plain_text()
        return fragment.value

    def _flatten_fragments(
        self,
        fragments: list[Text],
        theme: Theme,
        render_index: RenderIndex,
    ) -> str:
        return "".join(
            self._resolve_fragment_text(fragment, theme, render_index)
            for fragment in fragments
        )

    def _anchor_markup(self, anchor: str | None) -> str:
        if not anchor:
            return ""
        return f'<a name="{escape(anchor)}"/>'

    def _link_markup(
        self,
        target: str | None,
        inner_markup: str,
        *,
        internal: bool,
    ) -> str:
        if not target:
            return inner_markup
        href = f"#{target}" if internal else target
        return f'<a href="{escape(href)}">{inner_markup}</a>'

    def _block_reference_anchor(
        self,
        target: Table | Figure,
        render_index: RenderIndex,
    ) -> str | None:
        if isinstance(target, Table):
            return render_index.table_anchor(target)
        return render_index.figure_anchor(target)

    def _resolve_block_reference(self, target: Table | Figure, theme: Theme, render_index: RenderIndex) -> str:
        if isinstance(target, Table):
            number = render_index.table_number(target)
            if number is None:
                raise DocscriptorError("Table references require the target table to have a caption and be included in the document")
            return f"{theme.table_label} {number}"

        number = render_index.figure_number(target)
        if number is None:
            raise DocscriptorError("Figure references require the target figure to have a caption and be included in the document")
        return f"{theme.figure_label} {number}"

    def _caption_fragments(self, label: str, number: int | None, caption: Paragraph) -> list[Text]:
        if number is None:
            return caption.content
        return [Text(f"{label} {number}. ")] + caption.content

    def _render_caption_list(
        self,
        title: list[Text] | None,
        entries: list[object],
        theme: Theme,
        styles: object,
        render_index: RenderIndex,
        default_title: str,
        label: str,
    ) -> list[object]:
        level = theme.generated_section_level
        bold, italic = theme.heading_emphasis(level)
        title_style = RLParagraphStyle(
            "GeneratedCaptionListTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(level),
            leading=theme.heading_size(level) * 1.2,
            spaceBefore=12,
            spaceAfter=6,
            alignment=ALIGNMENTS[theme.heading_alignment(level)],
            textColor=colors.black,
        )
        entry_style = self._paragraph_style(ParagraphStyle(space_after=3), theme, styles["BodyText"])
        story: list[object] = [
            RLParagraph(
                self._inline_markup(
                    title or [Text(default_title)],
                    theme,
                    render_index,
                    base_font_name=title_style.fontName,
                    base_size=title_style.fontSize,
                    base_bold=bold,
                    base_italic=italic,
                ),
                title_style,
            )
        ]
        for entry in entries:
            story.append(
                RLParagraph(
                    self._link_markup(
                        entry.anchor,
                        self._inline_markup(
                            self._caption_fragments(
                                label,
                                entry.number,
                                entry.block.caption,
                            ),
                            theme,
                            render_index,
                            base_font_name=entry_style.fontName,
                            base_size=entry_style.fontSize,
                        ),
                        internal=True,
                    ),
                    entry_style,
                )
            )
        if entries:
            story.append(Spacer(1, 6))
        return story

    def _render_comments_page(
        self,
        title: list[Text] | None,
        theme: Theme,
        styles: object,
        render_index: RenderIndex,
    ) -> list[object]:
        level = theme.generated_section_level
        bold, italic = theme.heading_emphasis(level)
        title_style = RLParagraphStyle(
            "CommentsPageTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(level),
            leading=theme.heading_size(level) * 1.2,
            spaceBefore=0,
            spaceAfter=10,
            alignment=ALIGNMENTS[theme.heading_alignment(level)],
            textColor=colors.black,
        )
        entry_style = RLParagraphStyle(
            "CommentEntry",
            parent=styles["BodyText"],
            fontName=self._resolve_font(theme.body_font_name, False, False),
            fontSize=theme.body_font_size,
            leading=theme.body_font_size * 1.35,
            leftIndent=18,
            firstLineIndent=-18,
            spaceAfter=6,
            textColor=colors.black,
        )
        story: list[object] = [
            RLPageBreak(),
            RLParagraph(
                self._inline_markup(
                    title or [Text(theme.comments_title)],
                    theme,
                    render_index,
                    base_font_name=title_style.fontName,
                    base_size=title_style.fontSize,
                    base_bold=bold,
                    base_italic=italic,
                ),
                title_style,
            ),
        ]
        for entry in render_index.comments:
            story.append(
                RLParagraph(
                    self._inline_markup(
                        [Text(f"[{entry.number}] ")] + entry.comment.comment,
                        theme,
                        render_index,
                        base_font_name=entry_style.fontName,
                        base_size=entry_style.fontSize,
                    ),
                    entry_style,
                )
            )
        return story

    def _render_footnotes_page(
        self,
        title: list[Text] | None,
        theme: Theme,
        styles: object,
        render_index: RenderIndex,
    ) -> list[object]:
        level = theme.generated_section_level
        bold, italic = theme.heading_emphasis(level)
        title_style = RLParagraphStyle(
            "FootnotesPageTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(level),
            leading=theme.heading_size(level) * 1.2,
            spaceBefore=0,
            spaceAfter=10,
            alignment=ALIGNMENTS[theme.heading_alignment(level)],
            textColor=colors.black,
        )
        entry_style = RLParagraphStyle(
            "FootnoteEntry",
            parent=styles["BodyText"],
            fontName=self._resolve_font(theme.body_font_name, False, False),
            fontSize=theme.body_font_size,
            leading=theme.body_font_size * 1.35,
            leftIndent=18,
            firstLineIndent=-18,
            spaceAfter=6,
            textColor=colors.black,
        )
        story: list[object] = [
            RLPageBreak(),
            RLParagraph(
                self._inline_markup(
                    title or [Text(theme.footnotes_title)],
                    theme,
                    render_index,
                    base_font_name=title_style.fontName,
                    base_size=title_style.fontSize,
                    base_bold=bold,
                    base_italic=italic,
                ),
                title_style,
            ),
        ]
        for entry in render_index.footnotes:
            story.append(
                RLParagraph(
                    self._inline_markup(
                        [Text(f"[{entry.number}] ")] + entry.footnote.note,
                        theme,
                        render_index,
                        base_font_name=entry_style.fontName,
                        base_size=entry_style.fontSize,
                    ),
                    entry_style,
                )
            )
        return story

    def _render_references_page(
        self,
        title: list[Text] | None,
        theme: Theme,
        styles: object,
        render_index: RenderIndex,
    ) -> list[object]:
        level = theme.generated_section_level
        bold, italic = theme.heading_emphasis(level)
        title_style = RLParagraphStyle(
            "ReferencesPageTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(level),
            leading=theme.heading_size(level) * 1.2,
            spaceBefore=0,
            spaceAfter=10,
            alignment=ALIGNMENTS[theme.heading_alignment(level)],
            textColor=colors.black,
        )
        entry_style = RLParagraphStyle(
            "ReferenceEntry",
            parent=styles["BodyText"],
            fontName=self._resolve_font(theme.body_font_name, False, False),
            fontSize=theme.body_font_size,
            leading=theme.body_font_size * 1.35,
            leftIndent=18,
            firstLineIndent=-18,
            spaceAfter=6,
            textColor=colors.black,
        )
        story: list[object] = [
            RLPageBreak(),
            RLParagraph(
                self._inline_markup(
                    title or [Text(theme.references_title)],
                    theme,
                    render_index,
                    base_font_name=title_style.fontName,
                    base_size=title_style.fontSize,
                    base_bold=bold,
                    base_italic=italic,
                ),
                title_style,
            ),
        ]
        for entry in render_index.citations:
            story.append(
                RLParagraph(
                    self._anchor_markup(entry.anchor)
                    + self._inline_markup(
                        [Text(f"[{entry.number}] ")] + entry.source.reference_fragments(),
                        theme,
                        render_index,
                        base_font_name=entry_style.fontName,
                        base_size=entry_style.fontSize,
                    ),
                    entry_style,
                )
            )
        return story

    def _render_table_of_contents(
        self,
        block: TableOfContents,
        context: PdfRenderContext,
    ) -> list[object]:
        theme = context.theme
        styles = context.styles
        render_index = context.render_index
        level = theme.generated_section_level
        bold, italic = theme.heading_emphasis(level)
        title_style = RLParagraphStyle(
            "TableOfContentsTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(level),
            leading=theme.heading_size(level) * 1.2,
            spaceBefore=12,
            spaceAfter=6,
            alignment=ALIGNMENTS[theme.heading_alignment(level)],
            textColor=colors.black,
        )
        story: list[object] = [
            RLParagraph(
                self._inline_markup(
                    block.title or [Text(theme.contents_title)],
                    theme,
                    render_index,
                    base_font_name=title_style.fontName,
                    base_size=title_style.fontSize,
                    base_bold=bold,
                    base_italic=italic,
                ),
                title_style,
            )
        ]
        if block.show_page_numbers:
            toc = FilteredTableOfContents(
                max_level=block.max_level,
                dotsMinLevel=0 if block.leader else -1,
            )
            toc.levelStyles = [
                self._pdf_toc_level_style(block, toc_level, theme, styles)
                for toc_level in range(max((entry.level for entry in render_index.headings), default=1))
            ]
            story.append(toc)
        else:
            for entry in render_index.headings:
                if not block.includes_level(entry.level):
                    continue
                entry_style = self._pdf_toc_level_style(block, entry.level - 1, theme, styles)
                story.append(
                    RLParagraph(
                        self._link_markup(
                            entry.anchor,
                            self._inline_markup(
                                self._heading_fragments(entry.title, entry.number),
                                theme,
                                render_index,
                                base_font_name=entry_style.fontName,
                                base_size=entry_style.fontSize,
                            ),
                            internal=True,
                        ),
                        entry_style,
                    )
                )
        story.append(Spacer(1, 6))
        return story

    def _pdf_toc_level_style(
        self,
        block: TableOfContents,
        toc_level: int,
        theme: Theme,
        styles: object,
    ) -> RLParagraphStyle:
        level = toc_level + 1
        toc_style = self._toc_level_style(block, level)
        font_size = theme.body_font_size + toc_style.font_size_delta
        return RLParagraphStyle(
            f"TableOfContentsEntry{level}",
            parent=styles["BodyText"],
            fontName=self._resolve_font(
                theme.body_font_name,
                bool(toc_style.bold),
                bool(toc_style.italic),
            ),
            fontSize=font_size,
            leading=font_size * 1.32,
            leftIndent=20 * toc_style.indent / 0.24 if toc_style.indent else 0,
            spaceBefore=toc_style.space_before,
            spaceAfter=toc_style.space_after,
            textColor=colors.black,
        )

    def _toc_level_style(self, block: TableOfContents, level: int) -> TocLevelStyle:
        defaults = TocLevelStyle(
            indent=0.24 * max(level - 1, 0),
            space_before=12 if level == 1 else (3 if level == 2 else 0),
            space_after=7 if level == 1 else (3 if level == 2 else 2),
            font_size_delta=0.6 if level == 1 else 0,
            bold=True if level == 1 else False,
            italic=False,
        )
        override = block.style_for_level(level)
        return TocLevelStyle(
            indent=defaults.indent if override.indent is None else override.indent,
            space_before=defaults.space_before if override.space_before is None else override.space_before,
            space_after=defaults.space_after if override.space_after is None else override.space_after,
            font_size_delta=defaults.font_size_delta if override.font_size_delta is None else override.font_size_delta,
            bold=defaults.bold if override.bold is None else override.bold,
            italic=defaults.italic if override.italic is None else override.italic,
        )

    def _page_callback(self, theme: Theme, *, has_front_matter: bool):
        font_name = self._resolve_font(theme.body_font_name, False, False)

        def draw_page(canvas: object, doc: object) -> None:
            canvas.saveState()
            if theme.page_background_color != "FFFFFF":
                canvas.setFillColor(colors.HexColor(f"#{theme.page_background_color}"))
                canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
            if not theme.show_page_numbers:
                canvas.restoreState()
                return
            canvas.setFont(font_name, theme.page_number_font_size)
            current_page = canvas.getPageNumber()
            main_start_page = getattr(doc, "main_matter_start_page", None)
            is_front_matter = has_front_matter and (
                main_start_page is None or current_page < main_start_page
            )
            logical_page = (
                current_page
                if is_front_matter or main_start_page is None
                else current_page - main_start_page + 1
            )
            text = theme.format_page_number(
                logical_page,
                front_matter=is_front_matter,
            )
            y = 0.45 * inch
            if theme.page_number_alignment == "left":
                canvas.drawString(doc.leftMargin, y, text)
            elif theme.page_number_alignment == "right":
                canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, y, text)
            else:
                canvas.drawCentredString(doc.pagesize[0] / 2, y, text)
            canvas.restoreState()

        return draw_page

    def _comment_marker(self, fragment: Comment, render_index: RenderIndex) -> str:
        return f"[{render_index.comment_number(fragment)}]"

    def _footnote_marker(self, fragment: Footnote, render_index: RenderIndex) -> str:
        return str(render_index.footnote_number(fragment))
