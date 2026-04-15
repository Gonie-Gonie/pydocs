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
from reportlab.platypus import KeepTogether, ListFlowable, ListItem as RLListItem, Paragraph as RLParagraph, SimpleDocTemplate, Spacer, Table as RLTable, TableStyle

from docscriptor.model import Body, Document, Figure, ListBlock, Paragraph, ParagraphStyle, PathLike, Section, Table, Text, Theme


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


class PdfRenderer:
    """Render docscriptor documents into PDF files."""

    def render(self, document: Document, output_path: PathLike) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        pdf = SimpleDocTemplate(str(path), pagesize=A4, title=document.title, author=document.author)
        story: list[object] = []
        styles = getSampleStyleSheet()

        title_style = RLParagraphStyle(
            "DocscriptorTitle",
            parent=styles["Title"],
            fontName=self._resolve_font(document.theme.body_font_name, False, False),
            fontSize=document.theme.title_font_size,
            leading=document.theme.title_font_size * 1.2,
            spaceAfter=18,
            alignment=TA_CENTER,
        )
        story.append(RLParagraph(escape(document.title), title_style))

        for child in document.body.children:
            story.extend(self._render_block(child, document.theme, styles))

        pdf.build(story)
        return path

    def _render_block(self, block: object, theme: Theme, styles: object) -> list[object]:
        if isinstance(block, Body):
            story: list[object] = []
            for child in block.children:
                story.extend(self._render_block(child, theme, styles))
            return story
        if isinstance(block, Section):
            title_style = RLParagraphStyle(
                f"Heading{block.level}",
                parent=styles["Heading1"],
                fontName=self._resolve_font(theme.body_font_name, True, False),
                fontSize=theme.heading_size(block.level),
                leading=theme.heading_size(block.level) * 1.2,
                spaceBefore=12,
                spaceAfter=8,
            )
            story = [RLParagraph(self._inline_markup(block.title, theme), title_style)]
            for child in block.children:
                story.extend(self._render_block(child, theme, styles))
            return story
        if isinstance(block, Paragraph):
            paragraph_style = self._paragraph_style(block.style, theme, styles["BodyText"])
            return [RLParagraph(self._inline_markup(block.content, theme), paragraph_style)]
        if isinstance(block, ListBlock):
            return self._render_list(block, theme, styles)
        if isinstance(block, Table):
            return self._render_table(block, theme, styles)
        if isinstance(block, Figure):
            return self._render_figure(block, theme, styles)
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
        )

    def _render_table(self, block: Table, theme: Theme, styles: object) -> list[object]:
        body_style = self._paragraph_style(ParagraphStyle(space_after=0), theme, styles["BodyText"])
        header_style = RLParagraphStyle(
            "TableHeader",
            parent=body_style,
            fontName=self._resolve_font(theme.body_font_name, True, False),
        )

        table_rows: list[list[object]] = [
            [RLParagraph(self._inline_markup(cell.content, theme), header_style) for cell in block.headers]
        ]
        for row in block.rows:
            table_rows.append([RLParagraph(self._inline_markup(cell.content, theme), body_style) for cell in row])

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
            story.append(RLParagraph(self._inline_markup(block.caption.content, theme), caption_style))
        else:
            story.append(Spacer(1, 12))
        return story

    def _render_list(self, block: ListBlock, theme: Theme, styles: object) -> list[object]:
        item_style = self._paragraph_style(ParagraphStyle(space_after=3), theme, styles["BodyText"])
        list_items = [
            RLListItem(RLParagraph(self._inline_markup(item.content, theme), item_style))
            for item in block.items
        ]
        flowable = ListFlowable(
            list_items,
            bulletType="1" if block.ordered else "bullet",
            start="1",
            leftIndent=18,
        )
        return [flowable, Spacer(1, 8)]

    def _render_figure(self, block: Figure, theme: Theme, styles: object) -> list[object]:
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
            elements.append(RLParagraph(self._inline_markup(block.caption.content, theme), caption_style))
        else:
            elements.append(Spacer(1, 12))
        return [KeepTogether(elements)]

    def _inline_markup(self, fragments: list[Text], theme: Theme) -> str:
        parts: list[str] = []
        for fragment in fragments:
            text = escape(fragment.value).replace("\n", "<br/>")
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
        if font_name in PDF_FONT_VARIANTS:
            return PDF_FONT_VARIANTS[font_name][(bold, italic)]
        if font_name in pdfmetrics.getRegisteredFontNames():
            return font_name
        fallback = "Courier" if "Courier" in font_name else "Helvetica"
        return PDF_FONT_VARIANTS[fallback][(bold, italic)]
