"""PDF renderer."""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle as RLParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Image as RLImage
from reportlab.platypus import KeepTogether, ListFlowable, ListItem as RLListItem, PageBreak, Paragraph as RLParagraph, Preformatted, SimpleDocTemplate, Spacer, Table as RLTable, TableStyle

from docscriptor.model import (
    _BlockReference,
    Body,
    BulletList,
    Citation,
    CodeBlock,
    Document,
    DocscriptorError,
    Figure,
    FigureList,
    NumberedList,
    Paragraph,
    ParagraphStyle,
    PathLike,
    RenderIndex,
    ReferencesPage,
    Section,
    Table,
    TableList,
    Text,
    Theme,
    build_render_index,
)


ALIGNMENTS = {
    "left": TA_LEFT,
    "center": TA_CENTER,
    "right": TA_RIGHT,
    "justify": TA_JUSTIFY,
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
    "helvetica": "Helvetica",
    "arial": "Helvetica",
}


class PdfRenderer:
    """Render docscriptor documents into PDF files."""

    def render(self, document: Document, output_path: PathLike) -> Path:
        """Render a docscriptor document to a PDF file."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        pdf = SimpleDocTemplate(str(path), pagesize=A4, title=document.title, author=document.author)
        story: list[object] = []
        styles = getSampleStyleSheet()
        render_index = build_render_index(document)

        title_style = RLParagraphStyle(
            "DocscriptorTitle",
            parent=styles["Title"],
            fontName=self._resolve_font(document.theme.body_font_name, True, False),
            fontSize=document.theme.title_font_size,
            leading=document.theme.title_font_size * 1.2,
            spaceAfter=18,
            alignment=TA_CENTER,
            textColor=colors.black,
        )
        story.append(RLParagraph(escape(document.title), title_style))

        for child in document.body.children:
            story.extend(self._render_block(child, document.theme, styles, render_index))

        pdf.build(story)
        return path

    def _render_block(self, block: object, theme: Theme, styles: object, render_index: RenderIndex) -> list[object]:
        if isinstance(block, Body):
            story: list[object] = []
            for child in block.children:
                story.extend(self._render_block(child, theme, styles, render_index))
            return story
        if isinstance(block, Section):
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
            story = [RLParagraph(self._inline_markup(block.title, theme, render_index), title_style)]
            for child in block.children:
                story.extend(self._render_block(child, theme, styles, render_index))
            return story
        if isinstance(block, Paragraph):
            paragraph_style = self._paragraph_style(block.style, theme, styles["BodyText"])
            return [RLParagraph(self._inline_markup(block.content, theme, render_index), paragraph_style)]
        if isinstance(block, (BulletList, NumberedList)):
            return self._render_list(block, theme, styles, render_index)
        if isinstance(block, CodeBlock):
            return self._render_code_block(block, theme, styles)
        if isinstance(block, ReferencesPage):
            return self._render_references_page(block.title, theme, styles, render_index)
        if isinstance(block, TableList):
            return self._render_caption_list(block.title, render_index.tables, theme, styles, render_index, theme.list_of_tables_title, theme.table_label)
        if isinstance(block, FigureList):
            return self._render_caption_list(block.title, render_index.figures, theme, styles, render_index, theme.list_of_figures_title, theme.figure_label)
        if isinstance(block, Table):
            return self._render_table(block, theme, styles, render_index)
        if isinstance(block, Figure):
            return self._render_figure(block, theme, styles, render_index)
        raise TypeError(f"Unsupported block type for PDF rendering: {type(block)!r}")

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

    def _render_table(self, block: Table, theme: Theme, styles: object, render_index: RenderIndex) -> list[object]:
        body_style = self._paragraph_style(ParagraphStyle(space_after=0), theme, styles["BodyText"])
        header_style = RLParagraphStyle(
            "TableHeader",
            parent=body_style,
            fontName=self._resolve_font(theme.body_font_name, True, False),
        )

        table_rows: list[list[object]] = [
            [RLParagraph(self._inline_markup(cell.content, theme, render_index), header_style) for cell in block.headers]
        ]
        for row in block.rows:
            table_rows.append([RLParagraph(self._inline_markup(cell.content, theme, render_index), body_style) for cell in row])

        column_widths = [width * inch for width in block.column_widths] if block.column_widths is not None else None
        table = RLTable(table_rows, colWidths=column_widths, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EDF5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C2D0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story: list[object] = [table]
        if block.caption is not None:
            caption_style = RLParagraphStyle(
                "TableCaption",
                parent=body_style,
                fontSize=theme.caption_font_size,
                alignment=TA_CENTER,
                spaceBefore=6,
                spaceAfter=12,
            )
            story.append(
                RLParagraph(
                    self._inline_markup(self._caption_fragments(theme.table_label, render_index.table_number(block), block.caption), theme, render_index),
                    caption_style,
                )
            )
        else:
            story.append(Spacer(1, 12))
        return story

    def _render_list(self, block: BulletList | NumberedList, theme: Theme, styles: object, render_index: RenderIndex) -> list[object]:
        item_style = self._paragraph_style(ParagraphStyle(space_after=3), theme, styles["BodyText"])
        list_items = [
            RLListItem(RLParagraph(self._inline_markup(item.content, theme, render_index), item_style))
            for item in block.items
        ]
        list_kwargs: dict[str, object] = {
            "leftIndent": 18,
        }
        if isinstance(block, NumberedList):
            list_kwargs["bulletType"] = "1"
            list_kwargs["start"] = "1"
        else:
            list_kwargs["bulletType"] = "bullet"
        flowable = ListFlowable(list_items, **list_kwargs)
        return [flowable, Spacer(1, 8)]

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
                fontSize=theme.caption_font_size,
                spaceAfter=2,
            )
            elements.append(RLParagraph(escape(block.language.upper()), label_style))

        elements.append(Preformatted(block.code, code_style))
        return [KeepTogether(elements)]

    def _render_figure(self, block: Figure, theme: Theme, styles: object, render_index: RenderIndex) -> list[object]:
        image = RLImage(str(block.image_path))
        if block.width_inches is not None:
            target_width = block.width_inches * inch
            scale = target_width / image.drawWidth
            image.drawWidth = target_width
            image.drawHeight = image.drawHeight * scale

        body_style = self._paragraph_style(ParagraphStyle(space_after=0), theme, styles["BodyText"])
        elements: list[object] = [image]
        if block.caption is not None:
            caption_style = RLParagraphStyle(
                "FigureCaption",
                parent=body_style,
                fontSize=theme.caption_font_size,
                alignment=TA_CENTER,
                spaceBefore=6,
                spaceAfter=12,
            )
            elements.append(
                RLParagraph(
                    self._inline_markup(self._caption_fragments(theme.figure_label, render_index.figure_number(block), block.caption), theme, render_index),
                    caption_style,
                )
            )
        else:
            elements.append(Spacer(1, 12))
        return [KeepTogether(elements)]

    def _inline_markup(self, fragments: list[Text], theme: Theme, render_index: RenderIndex) -> str:
        parts: list[str] = []
        for fragment in fragments:
            text = escape(self._resolve_fragment_text(fragment, theme, render_index)).replace("\n", "<br/>")
            font_name = self._resolve_font(
                fragment.style.font_name or theme.body_font_name,
                bool(fragment.style.bold),
                bool(fragment.style.italic),
            )
            size = fragment.style.font_size or theme.body_font_size

            font_attrs = [f'face="{font_name}"', f'size="{size}"']
            if fragment.style.color is not None:
                font_attrs.append(f'color="#{fragment.style.color}"')
            wrapped = f"<font {' '.join(font_attrs)}>{text}</font>"
            if fragment.style.underline:
                wrapped = f"<u>{wrapped}</u>"
            parts.append(wrapped)
        return "".join(parts) or "&nbsp;"

    def _resolve_font(self, font_name: str, bold: bool, italic: bool) -> str:
        aliased_font_name = FONT_FAMILY_ALIASES.get(font_name.lower(), font_name)
        font_name = aliased_font_name
        if font_name in PDF_FONT_VARIANTS:
            return PDF_FONT_VARIANTS[font_name][(bold, italic)]
        if font_name in pdfmetrics.getRegisteredFontNames():
            return font_name
        fallback = "Courier" if "Courier" in font_name else "Times-Roman" if "Times" in font_name else "Helvetica"
        return PDF_FONT_VARIANTS[fallback][(bold, italic)]

    def _resolve_fragment_text(self, fragment: Text, theme: Theme, render_index: RenderIndex) -> str:
        if isinstance(fragment, _BlockReference):
            return self._resolve_block_reference(fragment.target, theme, render_index)
        if isinstance(fragment, Citation):
            return f"[{render_index.citation_number(fragment.target)}]"
        return fragment.value

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
        bold, italic = theme.heading_emphasis(4)
        title_style = RLParagraphStyle(
            "GeneratedCaptionListTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(4),
            leading=theme.heading_size(4) * 1.2,
            spaceBefore=12,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor=colors.black,
        )
        entry_style = self._paragraph_style(ParagraphStyle(space_after=3), theme, styles["BodyText"])
        story: list[object] = [RLParagraph(self._inline_markup(title or [Text(default_title)], theme, render_index), title_style)]
        for entry in entries:
            story.append(
                RLParagraph(
                    self._inline_markup(self._caption_fragments(label, entry.number, entry.block.caption), theme, render_index),
                    entry_style,
                )
            )
        if entries:
            story.append(Spacer(1, 6))
        return story

    def _render_references_page(
        self,
        title: list[Text] | None,
        theme: Theme,
        styles: object,
        render_index: RenderIndex,
    ) -> list[object]:
        bold, italic = theme.heading_emphasis(1)
        title_style = RLParagraphStyle(
            "ReferencesPageTitle",
            parent=styles["Heading1"],
            fontName=self._resolve_font(theme.body_font_name, bold, italic),
            fontSize=theme.heading_size(1),
            leading=theme.heading_size(1) * 1.2,
            spaceBefore=0,
            spaceAfter=10,
            alignment=ALIGNMENTS[theme.heading_alignment(1)],
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
        story: list[object] = [PageBreak(), RLParagraph(self._inline_markup(title or [Text(theme.references_title)], theme, render_index), title_style)]
        for entry in render_index.citations:
            story.append(RLParagraph(escape(f"[{entry.number}] {entry.source.format_reference()}"), entry_style))
        return story
