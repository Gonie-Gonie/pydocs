"""DOCX renderer."""

from __future__ import annotations

from pathlib import Path

from docx import Document as WordDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

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
        render_index = build_render_index(document)
        self._configure_document(word_document, document)
        self._add_heading(word_document, [Text(document.title)], level=0, theme=document.theme)

        for child in document.body.children:
            self._render_block(word_document, child, document.theme, render_index)

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

    def _render_block(self, word_document: WordDocument, block: object, theme: Theme, render_index: RenderIndex) -> None:
        if isinstance(block, Body):
            for child in block.children:
                self._render_block(word_document, child, theme, render_index)
            return
        if isinstance(block, Section):
            self._add_heading(word_document, block.title, block.level, theme)
            for child in block.children:
                self._render_block(word_document, child, theme, render_index)
            return
        if isinstance(block, Paragraph):
            paragraph = word_document.add_paragraph()
            self._apply_paragraph_style(paragraph, block.style)
            self._append_runs(paragraph, block.content, theme=theme, render_index=render_index)
            return
        if isinstance(block, (BulletList, NumberedList)):
            self._render_list(word_document, block, theme, render_index)
            return
        if isinstance(block, CodeBlock):
            self._render_code_block(word_document, block, theme)
            return
        if isinstance(block, ReferencesPage):
            self._render_references_page(word_document, block.title, theme, render_index)
            return
        if isinstance(block, TableList):
            self._render_caption_list(word_document, block.title, render_index.tables, theme, render_index, theme.list_of_tables_title, theme.table_label)
            return
        if isinstance(block, FigureList):
            self._render_caption_list(word_document, block.title, render_index.figures, theme, render_index, theme.list_of_figures_title, theme.figure_label)
            return
        if isinstance(block, Table):
            self._render_table(word_document, block, theme, render_index)
            return
        if isinstance(block, Figure):
            self._render_figure(word_document, block, theme, render_index)
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

    def _append_runs(
        self,
        paragraph: object,
        fragments: list[Text],
        default_size: float | None = None,
        *,
        theme: Theme | None = None,
        render_index: RenderIndex | None = None,
    ) -> None:
        for fragment in fragments:
            run = paragraph.add_run(self._resolve_fragment_text(fragment, theme, render_index))
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

    def _render_list(self, word_document: WordDocument, list_block: BulletList | NumberedList, theme: Theme, render_index: RenderIndex) -> None:
        style_name = "List Number" if isinstance(list_block, NumberedList) else "List Bullet"
        for item in list_block.items:
            paragraph = word_document.add_paragraph(style=style_name)
            self._apply_paragraph_style(paragraph, item.style)
            self._append_runs(paragraph, item.content, theme=theme, render_index=render_index)

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

    def _render_table(self, word_document: WordDocument, table_block: Table, theme: Theme, render_index: RenderIndex) -> None:
        row_count = len(table_block.rows) + 1
        table = word_document.add_table(rows=row_count, cols=len(table_block.headers))
        table.style = "Table Grid"

        for column_index, header in enumerate(table_block.headers):
            paragraph = table.rows[0].cells[column_index].paragraphs[0]
            self._append_runs(paragraph, header.content or [Text("")], theme=theme, render_index=render_index)
            for run in paragraph.runs:
                run.bold = True

        for row_index, row in enumerate(table_block.rows, start=1):
            for column_index, cell in enumerate(row):
                paragraph = table.rows[row_index].cells[column_index].paragraphs[0]
                self._append_runs(paragraph, cell.content or [Text("")], theme=theme, render_index=render_index)

        if table_block.caption is not None:
            caption = word_document.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._append_runs(
                caption,
                self._caption_fragments(theme.table_label, render_index.table_number(table_block), table_block.caption),
                default_size=theme.caption_font_size,
                theme=theme,
                render_index=render_index,
            )

    def _render_figure(self, word_document: WordDocument, figure: Figure, theme: Theme, render_index: RenderIndex) -> None:
        paragraph = word_document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        width = Inches(figure.width_inches) if figure.width_inches is not None else None
        run.add_picture(str(figure.image_path), width=width)

        if figure.caption is not None:
            caption = word_document.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._append_runs(
                caption,
                self._caption_fragments(theme.figure_label, render_index.figure_number(figure), figure.caption),
                default_size=theme.caption_font_size,
                theme=theme,
                render_index=render_index,
            )

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

    def _resolve_fragment_text(self, fragment: Text, theme: Theme | None, render_index: RenderIndex | None) -> str:
        if isinstance(fragment, _BlockReference):
            if theme is None or render_index is None:
                return fragment.plain_text()
            return self._resolve_block_reference(fragment.target, theme, render_index)
        if isinstance(fragment, Citation):
            if render_index is None:
                return fragment.plain_text()
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
        word_document: WordDocument,
        title: list[Text] | None,
        entries: list[object],
        theme: Theme,
        render_index: RenderIndex,
        default_title: str,
        label: str,
    ) -> None:
        self._add_heading(word_document, title or [Text(default_title)], level=4, theme=theme)
        for entry in entries:
            paragraph = word_document.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.25)
            self._append_runs(
                paragraph,
                self._caption_fragments(label, entry.number, entry.block.caption),
                default_size=theme.caption_font_size,
                theme=theme,
                render_index=render_index,
            )

    def _render_references_page(
        self,
        word_document: WordDocument,
        title: list[Text] | None,
        theme: Theme,
        render_index: RenderIndex,
    ) -> None:
        word_document.add_page_break()
        self._add_heading(word_document, title or [Text(theme.references_title)], level=1, theme=theme)
        for entry in render_index.citations:
            paragraph = word_document.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.3)
            paragraph.paragraph_format.first_line_indent = Inches(-0.3)
            self._append_runs(
                paragraph,
                [Text(f"[{entry.number}] {entry.source.format_reference()}")],
                default_size=theme.body_font_size,
                theme=theme,
                render_index=render_index,
            )
