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
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as RLImage
from reportlab.platypus import KeepTogether, PageBreak, Paragraph as RLParagraph, Preformatted, SimpleDocTemplate, Spacer, Table as RLTable, TableStyle

from docscriptor.equations import SUBSCRIPT, SUPERSCRIPT, parse_latex_segments
from docscriptor.model import (
    _BlockReference,
    Body,
    Box,
    BulletList,
    Citation,
    Comment,
    CommentsPage,
    CodeBlock,
    Document,
    DocscriptorError,
    Equation,
    Figure,
    FigureList,
    Math,
    NumberedList,
    Paragraph,
    ParagraphStyle,
    PathLike,
    RenderIndex,
    ReferencesPage,
    Section,
    Table,
    TableOfContents,
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


class PdfRenderer:
    """Render docscriptor documents into PDF files."""

    def __init__(self) -> None:
        self._registered_system_fonts: dict[tuple[str, bool, bool], str] = {}

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
        story.append(
            RLParagraph(
                self._inline_markup(
                    [Text(document.title)],
                    document.theme,
                    render_index,
                    base_font_name=title_style.fontName,
                    base_size=title_style.fontSize,
                    base_bold=True,
                    base_italic=False,
                ),
                title_style,
            )
        )

        for child in document.body.children:
            story.extend(self._render_block(child, document.theme, styles, render_index))

        if document.theme.show_page_numbers:
            page_callback = self._page_number_callback(document.theme)
            pdf.build(story, onFirstPage=page_callback, onLaterPages=page_callback)
        else:
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
            story = [
                RLParagraph(
                    self._inline_markup(
                        self._heading_fragments(block.title, render_index.heading_number(block)),
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
            for child in block.children:
                story.extend(self._render_block(child, theme, styles, render_index))
            return story
        if isinstance(block, Paragraph):
            paragraph_style = self._paragraph_style(block.style, theme, styles["BodyText"])
            return [
                RLParagraph(
                    self._inline_markup(
                        block.content,
                        theme,
                        render_index,
                        base_font_name=paragraph_style.fontName,
                        base_size=paragraph_style.fontSize,
                    ),
                    paragraph_style,
                )
            ]
        if isinstance(block, (BulletList, NumberedList)):
            return self._render_list(block, theme, styles, render_index)
        if isinstance(block, CodeBlock):
            return self._render_code_block(block, theme, styles)
        if isinstance(block, Equation):
            return self._render_equation(block, theme, styles)
        if isinstance(block, Box):
            return self._render_box(block, theme, styles, render_index)
        if isinstance(block, CommentsPage):
            return self._render_comments_page(block.title, theme, styles, render_index)
        if isinstance(block, ReferencesPage):
            return self._render_references_page(block.title, theme, styles, render_index)
        if isinstance(block, TableOfContents):
            return self._render_table_of_contents(block.title, theme, styles, render_index)
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
            [
                RLParagraph(
                    self._inline_markup(
                        cell.content,
                        theme,
                        render_index,
                        base_font_name=header_style.fontName,
                        base_size=header_style.fontSize,
                        base_bold=True,
                        base_italic=False,
                    ),
                    header_style,
                )
                for cell in block.headers
            ]
        ]
        for row in block.rows:
            table_rows.append(
                [
                    RLParagraph(
                        self._inline_markup(
                            cell.content,
                            theme,
                            render_index,
                            base_font_name=body_style.fontName,
                            base_size=body_style.fontSize,
                        ),
                        body_style,
                    )
                    for cell in row
                ]
            )

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
                    self._inline_markup(
                        self._caption_fragments(theme.table_label, render_index.table_number(block), block.caption),
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

    def _render_box(self, block: Box, theme: Theme, styles: object, render_index: RenderIndex) -> list[object]:
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
            for flowable in self._render_block(child, theme, styles, render_index):
                if isinstance(flowable, KeepTogether):
                    rows.extend([[nested]] for nested in flowable._content)
                    continue
                rows.append([flowable])
        if not rows:
            rows.append([Spacer(1, 1)])

        table = RLTable(rows, hAlign="LEFT", repeatRows=0)
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
                fontSize=theme.caption_font_size,
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
                    self._inline_markup(
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
        if isinstance(fragment, Comment):
            return fragment.value
        if isinstance(fragment, Math):
            return fragment.plain_text()
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
                    self._inline_markup(
                        self._caption_fragments(label, entry.number, entry.block.caption),
                        theme,
                        render_index,
                        base_font_name=entry_style.fontName,
                        base_size=entry_style.fontSize,
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
            PageBreak(),
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
            PageBreak(),
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
            story.append(RLParagraph(escape(f"[{entry.number}] {entry.source.format_reference()}"), entry_style))
        return story

    def _render_table_of_contents(
        self,
        title: list[Text] | None,
        theme: Theme,
        styles: object,
        render_index: RenderIndex,
    ) -> list[object]:
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
                    title or [Text(theme.contents_title)],
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
        for entry in render_index.headings:
            entry_style = RLParagraphStyle(
                f"TableOfContentsEntry{entry.level}",
                parent=styles["BodyText"],
                fontName=self._resolve_font(theme.body_font_name, False, False),
                fontSize=theme.body_font_size,
                leading=theme.body_font_size * 1.3,
                leftIndent=18 * max(entry.level - 1, 0),
                spaceAfter=3,
                textColor=colors.black,
            )
            story.append(
                RLParagraph(
                    self._inline_markup(
                        self._heading_fragments(entry.title, entry.number),
                        theme,
                        render_index,
                        base_font_name=entry_style.fontName,
                        base_size=entry_style.fontSize,
                    ),
                    entry_style,
                )
            )
        story.append(Spacer(1, 6))
        return story

    def _page_number_callback(self, theme: Theme):
        font_name = self._resolve_font(theme.body_font_name, False, False)

        def draw_page_number(canvas: object, doc: object) -> None:
            canvas.saveState()
            canvas.setFont(font_name, theme.page_number_font_size)
            text = theme.format_page_number(canvas.getPageNumber())
            y = 0.45 * inch
            if theme.page_number_alignment == "left":
                canvas.drawString(doc.leftMargin, y, text)
            elif theme.page_number_alignment == "right":
                canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, y, text)
            else:
                canvas.drawCentredString(doc.pagesize[0] / 2, y, text)
            canvas.restoreState()

        return draw_page_number

    def _comment_marker(self, fragment: Comment, render_index: RenderIndex) -> str:
        return f"[{render_index.comment_number(fragment)}]"
