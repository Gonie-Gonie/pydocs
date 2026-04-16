"""DOCX renderer."""

from __future__ import annotations

from pathlib import Path

from docx import Document as WordDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from docscriptor.model import Body, BulletList, CodeBlock, Document, Figure, NumberedList, Paragraph, ParagraphStyle, PathLike, Section, Table, Text, Theme


ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


class DocxRenderer:
    """Render docscriptor documents into DOCX files."""

    def render(self, document: Document, output_path: PathLike) -> Path:
        """Render a docscriptor document to a DOCX file."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        word_document = WordDocument()
        self._configure_document(word_document, document)
        self._add_heading(word_document, [Text(document.title)], level=0, theme=document.theme)

        for child in document.body.children:
            self._render_block(word_document, child, document.theme)

        word_document.save(path)
        return path

    def _configure_document(self, word_document: WordDocument, document: Document) -> None:
        properties = word_document.core_properties
        properties.title = document.title
        if document.author:
            properties.author = document.author
        if document.summary:
            properties.subject = document.summary

        normal_style = word_document.styles["Normal"]
        normal_style.font.name = document.theme.body_font_name
        normal_style.font.size = Pt(document.theme.body_font_size)
        normal_style.font.color.rgb = RGBColor(0, 0, 0)

        self._configure_named_style(
            word_document,
            "Title",
            font_name=document.theme.body_font_name,
            font_size=document.theme.title_font_size,
            bold=True,
            italic=False,
        )
        for level in range(1, 5):
            bold, italic = document.theme.heading_emphasis(level)
            self._configure_named_style(
                word_document,
                f"Heading {level}",
                font_name=document.theme.body_font_name,
                font_size=document.theme.heading_size(level),
                bold=bold,
                italic=italic,
            )

    def _render_block(self, word_document: WordDocument, block: object, theme: Theme) -> None:
        if isinstance(block, Body):
            for child in block.children:
                self._render_block(word_document, child, theme)
            return
        if isinstance(block, Section):
            self._add_heading(word_document, block.title, block.level, theme)
            for child in block.children:
                self._render_block(word_document, child, theme)
            return
        if isinstance(block, Paragraph):
            paragraph = word_document.add_paragraph()
            self._apply_paragraph_style(paragraph, block.style)
            self._append_runs(paragraph, block.content)
            return
        if isinstance(block, (BulletList, NumberedList)):
            self._render_list(word_document, block)
            return
        if isinstance(block, CodeBlock):
            self._render_code_block(word_document, block, theme)
            return
        if isinstance(block, Table):
            self._render_table(word_document, block)
            return
        if isinstance(block, Figure):
            self._render_figure(word_document, block)
            return
        raise TypeError(f"Unsupported block type for DOCX rendering: {type(block)!r}")

    def _add_heading(self, word_document: WordDocument, title: list[Text], level: int, theme: Theme) -> None:
        paragraph = word_document.add_paragraph()
        paragraph.style = "Title" if level == 0 else f"Heading {min(level, 9)}"
        if level == 0:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            paragraph.alignment = ALIGNMENTS[theme.heading_alignment(level)]
            paragraph.paragraph_format.space_before = Pt(18 if level == 1 else 12)
            paragraph.paragraph_format.space_after = Pt(10 if level == 1 else 6)
        self._append_runs(paragraph, title, default_size=theme.title_font_size if level == 0 else theme.heading_size(level))

    def _apply_paragraph_style(self, paragraph: object, style: ParagraphStyle) -> None:
        paragraph.alignment = ALIGNMENTS[style.alignment]
        if style.space_after is not None:
            paragraph.paragraph_format.space_after = Pt(style.space_after)
        if style.leading is not None:
            paragraph.paragraph_format.line_spacing = Pt(style.leading)

    def _append_runs(self, paragraph: object, fragments: list[Text], default_size: float | None = None) -> None:
        for fragment in fragments:
            run = paragraph.add_run(fragment.value)
            font = run.font
            if fragment.style.font_name:
                font.name = fragment.style.font_name
            if fragment.style.font_size is not None:
                font.size = Pt(fragment.style.font_size)
            elif default_size is not None:
                font.size = Pt(default_size)
            if fragment.style.bold is not None:
                font.bold = fragment.style.bold
            if fragment.style.italic is not None:
                font.italic = fragment.style.italic
            if fragment.style.underline is not None:
                font.underline = fragment.style.underline
            if fragment.style.color is not None:
                font.color.rgb = RGBColor.from_string(fragment.style.color)

    def _render_list(self, word_document: WordDocument, list_block: BulletList | NumberedList) -> None:
        style_name = "List Number" if isinstance(list_block, NumberedList) else "List Bullet"
        for item in list_block.items:
            paragraph = word_document.add_paragraph(style=style_name)
            self._apply_paragraph_style(paragraph, item.style)
            self._append_runs(paragraph, item.content)

    def _render_code_block(self, word_document: WordDocument, code_block: CodeBlock, theme: Theme) -> None:
        if code_block.language:
            label = word_document.add_paragraph()
            label.paragraph_format.space_after = Pt(2)
            run = label.add_run(code_block.language.upper())
            run.font.name = theme.monospace_font_name
            run.font.size = Pt(theme.caption_font_size)
            run.font.bold = True

        paragraph = word_document.add_paragraph()
        self._apply_paragraph_style(paragraph, code_block.style)
        paragraph.paragraph_format.left_indent = Inches(0.25)
        paragraph.paragraph_format.right_indent = Inches(0.1)
        paragraph.paragraph_format.space_before = Pt(6)
        self._set_paragraph_shading(paragraph, "F5F7FA")

        run = paragraph.add_run()
        run.font.name = theme.monospace_font_name
        run.font.size = Pt(max(theme.body_font_size - 1, 8))

        for index, line in enumerate(code_block.code.replace("\r\n", "\n").replace("\r", "\n").split("\n")):
            if index:
                run.add_break()
            run.add_text(line)

    def _render_table(self, word_document: WordDocument, table_block: Table) -> None:
        row_count = len(table_block.rows) + 1
        table = word_document.add_table(rows=row_count, cols=len(table_block.headers))
        table.style = "Table Grid"

        for column_index, header in enumerate(table_block.headers):
            paragraph = table.rows[0].cells[column_index].paragraphs[0]
            self._append_runs(paragraph, header.content or [Text("")])
            for run in paragraph.runs:
                run.bold = True

        for row_index, row in enumerate(table_block.rows, start=1):
            for column_index, cell in enumerate(row):
                paragraph = table.rows[row_index].cells[column_index].paragraphs[0]
                self._append_runs(paragraph, cell.content or [Text("")])

        if table_block.caption is not None:
            caption = word_document.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._append_runs(caption, table_block.caption.content)

    def _render_figure(self, word_document: WordDocument, figure: Figure) -> None:
        paragraph = word_document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        width = Inches(figure.width_inches) if figure.width_inches is not None else None
        run.add_picture(str(figure.image_path), width=width)

        if figure.caption is not None:
            caption = word_document.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._append_runs(caption, figure.caption.content)

    def _set_paragraph_shading(self, paragraph: object, fill: str) -> None:
        paragraph_properties = paragraph._p.get_or_add_pPr()
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), fill)
        paragraph_properties.append(shading)

    def _configure_named_style(
        self,
        word_document: WordDocument,
        style_name: str,
        *,
        font_name: str,
        font_size: float,
        bold: bool,
        italic: bool,
    ) -> None:
        style = word_document.styles[style_name]
        style.font.name = font_name
        style.font.size = Pt(font_size)
        style.font.bold = bold
        style.font.italic = italic
        style.font.color.rgb = RGBColor(0, 0, 0)
