"""DOCX renderer."""

from __future__ import annotations

from pathlib import Path

from docx import Document as WordDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

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
        self._initialized_cells: set[int] = set()
        render_index = build_render_index(document)
        self._configure_document(word_document, document)
        self._add_heading(word_document, [Text(document.title)], level=0, theme=document.theme)

        for child in document.body.children:
            self._render_block(word_document, child, document.theme, render_index, word_document=word_document)

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
        footer_style = word_document.styles["Footer"]
        footer_style.font.name = document.theme.body_font_name
        footer_style.font.size = Pt(document.theme.page_number_font_size)
        footer_style.font.color.rgb = RGBColor(0, 0, 0)

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
        if document.theme.show_page_numbers:
            self._add_page_number_footer(word_document, document.theme)

    def _render_block(
        self,
        container: object,
        block: object,
        theme: Theme,
        render_index: RenderIndex,
        *,
        word_document: WordDocument,
    ) -> None:
        if isinstance(block, Body):
            for child in block.children:
                self._render_block(container, child, theme, render_index, word_document=word_document)
            return
        if isinstance(block, Section):
            self._add_heading(
                container,
                block.title,
                block.level,
                theme,
                number_label=render_index.heading_number(block),
            )
            for child in block.children:
                self._render_block(container, child, theme, render_index, word_document=word_document)
            return
        if isinstance(block, Paragraph):
            paragraph = self._add_paragraph(container)
            self._apply_paragraph_style(paragraph, block.style)
            self._append_runs(paragraph, block.content, theme=theme, render_index=render_index, word_document=word_document)
            return
        if isinstance(block, (BulletList, NumberedList)):
            self._render_list(container, block, theme, render_index, word_document=word_document)
            return
        if isinstance(block, CodeBlock):
            self._render_code_block(container, block, theme)
            return
        if isinstance(block, Equation):
            self._render_equation(container, block, theme)
            return
        if isinstance(block, Box):
            self._render_box(container, block, theme, render_index, word_document=word_document)
            return
        if isinstance(block, CommentsPage):
            self._assert_document_container(container, "CommentsPage")
            self._render_comments_page(word_document, block.title, theme, render_index)
            return
        if isinstance(block, ReferencesPage):
            self._assert_document_container(container, "ReferencesPage")
            self._render_references_page(word_document, block.title, theme, render_index)
            return
        if isinstance(block, TableOfContents):
            self._assert_document_container(container, "TableOfContents")
            self._render_table_of_contents(word_document, block.title, theme, render_index)
            return
        if isinstance(block, TableList):
            self._assert_document_container(container, "TableList")
            self._render_caption_list(word_document, block.title, render_index.tables, theme, render_index, theme.list_of_tables_title, theme.table_label)
            return
        if isinstance(block, FigureList):
            self._assert_document_container(container, "FigureList")
            self._render_caption_list(word_document, block.title, render_index.figures, theme, render_index, theme.list_of_figures_title, theme.figure_label)
            return
        if isinstance(block, Table):
            self._render_table(container, block, theme, render_index, word_document=word_document)
            return
        if isinstance(block, Figure):
            self._render_figure(container, block, theme, render_index, word_document=word_document)
            return
        raise TypeError(f"Unsupported block type for DOCX rendering: {type(block)!r}")

    def _add_heading(
        self,
        container: object,
        title: list[Text],
        level: int,
        theme: Theme,
        *,
        number_label: str | None = None,
    ) -> None:
        paragraph = self._add_paragraph(container)
        paragraph.style = "Title" if level == 0 else f"Heading {min(level, 9)}"
        if level == 0:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            paragraph.alignment = ALIGNMENTS[theme.heading_alignment(level)]
            paragraph.paragraph_format.space_before = Pt(18 if level == 1 else 12)
            paragraph.paragraph_format.space_after = Pt(10 if level == 1 else 6)
        self._append_runs(
            paragraph,
            self._heading_fragments(title, number_label),
            default_size=theme.title_font_size if level == 0 else theme.heading_size(level),
            theme=theme,
        )

    def _add_paragraph(self, container: object) -> object:
        if self._is_cell_container(container):
            container_id = id(container)
            if container_id not in self._initialized_cells and container.paragraphs:
                self._initialized_cells.add(container_id)
                return container.paragraphs[0]
            self._initialized_cells.add(container_id)
        return container.add_paragraph()

    def _is_cell_container(self, container: object) -> bool:
        return hasattr(container, "_tc") and hasattr(container, "add_table")

    def _assert_document_container(self, container: object, block_name: str) -> None:
        if self._is_cell_container(container):
            raise DocscriptorError(f"{block_name} cannot be rendered inside a Box")

    def _heading_fragments(self, title: list[Text], number_label: str | None) -> list[Text]:
        if not number_label:
            return title
        return [Text(f"{number_label} ")] + title

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
        word_document: WordDocument | None = None,
    ) -> None:
        for fragment in fragments:
            if isinstance(fragment, Comment):
                self._append_comment_runs(
                    paragraph,
                    fragment,
                    default_size=default_size,
                    theme=theme,
                    render_index=render_index,
                    word_document=word_document,
                )
                continue
            if isinstance(fragment, Math):
                self._append_math_runs(paragraph, fragment, default_size=default_size)
                continue
            run = paragraph.add_run(self._resolve_fragment_text(fragment, theme, render_index))
            self._apply_run_style(run, fragment.style, default_size=default_size)

    def _apply_run_style(self, run: object, style: object, *, default_size: float | None = None) -> None:
        font = run.font
        if style.font_name:
            font.name = style.font_name
        if style.font_size is not None:
            font.size = Pt(style.font_size)
        elif default_size is not None:
            font.size = Pt(default_size)
        if style.bold is not None:
            font.bold = style.bold
        if style.italic is not None:
            font.italic = style.italic
        if style.underline is not None:
            font.underline = style.underline
        if style.color is not None:
            font.color.rgb = RGBColor.from_string(style.color)

    def _append_comment_runs(
        self,
        paragraph: object,
        fragment: Comment,
        *,
        default_size: float | None,
        theme: Theme | None,
        render_index: RenderIndex | None,
        word_document: WordDocument | None,
    ) -> None:
        visible_runs: list[object] = []
        if fragment.value:
            visible_run = paragraph.add_run(fragment.value)
            self._apply_run_style(visible_run, fragment.style, default_size=default_size)
            visible_runs.append(visible_run)

        marker_run = paragraph.add_run(self._comment_marker(fragment, render_index))
        self._apply_run_style(marker_run, fragment.style, default_size=max((default_size or 10.0) - 2, 8))
        marker_run.font.superscript = True
        anchor_runs = visible_runs or [marker_run]
        if word_document is not None and render_index is not None:
            word_document.add_comment(
                anchor_runs,
                text=self._flatten_fragments(fragment.comment, theme, render_index),
                author=fragment.author or "",
                initials=fragment.initials,
            )

    def _append_math_runs(self, paragraph: object, fragment: Math, *, default_size: float | None = None) -> None:
        for segment in parse_latex_segments(fragment.value):
            run = paragraph.add_run(segment.text)
            self._apply_run_style(run, fragment.style, default_size=default_size)
            if segment.vertical_align == SUPERSCRIPT:
                run.font.superscript = True
            elif segment.vertical_align == SUBSCRIPT:
                run.font.subscript = True

    def _render_list(
        self,
        container: object,
        list_block: BulletList | NumberedList,
        theme: Theme,
        render_index: RenderIndex,
        *,
        word_document: WordDocument,
    ) -> None:
        list_style = list_block.style or theme.list_style(ordered=isinstance(list_block, NumberedList))
        for index, item in enumerate(list_block.items):
            paragraph = self._add_paragraph(container)
            self._apply_paragraph_style(paragraph, item.style)
            paragraph.paragraph_format.left_indent = Inches(list_style.indent)
            paragraph.paragraph_format.first_line_indent = Inches(-list_style.indent)
            marker = list_style.marker_for(index)
            if marker:
                marker_run = paragraph.add_run(f"{marker} ")
                self._apply_run_style(marker_run, Text("").style, default_size=theme.body_font_size)
            self._append_runs(paragraph, item.content, theme=theme, render_index=render_index, word_document=word_document)

    def _render_code_block(self, container: object, code_block: CodeBlock, theme: Theme) -> None:
        if code_block.language:
            label = self._add_paragraph(container)
            label.paragraph_format.space_after = Pt(2)
            run = label.add_run(code_block.language.upper())
            run.font.name = theme.monospace_font_name
            run.font.size = Pt(theme.caption_font_size)
            run.font.bold = True

        paragraph = self._add_paragraph(container)
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

    def _render_equation(self, container: object, equation: Equation, theme: Theme) -> None:
        paragraph = self._add_paragraph(container)
        self._apply_paragraph_style(paragraph, equation.style)
        if paragraph.alignment is None:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._append_math_runs(
            paragraph,
            Math(equation.expression),
            default_size=max(theme.body_font_size + 1, 12),
        )

    def _render_box(
        self,
        container: object,
        box: Box,
        theme: Theme,
        render_index: RenderIndex,
        *,
        word_document: WordDocument,
    ) -> None:
        outer_table = container.add_table(rows=1, cols=1)
        cell = outer_table.rows[0].cells[0]
        cell._tc.clear_content()
        self._initialized_cells.discard(id(cell))
        self._set_cell_shading(cell, box.style.background_color)
        self._set_cell_borders(cell, box.style.border_color, box.style.border_width)
        self._set_cell_padding(cell, box.style.padding)

        if box.title is not None:
            title_paragraph = self._add_paragraph(cell)
            title_paragraph.paragraph_format.space_after = Pt(6)
            if box.style.title_background_color is not None:
                self._set_paragraph_shading(title_paragraph, box.style.title_background_color)
            self._append_runs(
                title_paragraph,
                box.title,
                default_size=theme.body_font_size,
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )

        for child in box.children:
            self._render_block(cell, child, theme, render_index, word_document=word_document)

        if not cell.paragraphs:
            cell.add_paragraph()

    def _render_table(
        self,
        container: object,
        table_block: Table,
        theme: Theme,
        render_index: RenderIndex,
        *,
        word_document: WordDocument,
    ) -> None:
        row_count = len(table_block.rows) + 1
        table = container.add_table(rows=row_count, cols=len(table_block.headers))
        table.style = "Table Grid"

        for column_index, header in enumerate(table_block.headers):
            paragraph = table.rows[0].cells[column_index].paragraphs[0]
            self._append_runs(
                paragraph,
                header.content or [Text("")],
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )
            for run in paragraph.runs:
                run.bold = True

        for row_index, row in enumerate(table_block.rows, start=1):
            for column_index, cell in enumerate(row):
                paragraph = table.rows[row_index].cells[column_index].paragraphs[0]
                self._append_runs(
                    paragraph,
                    cell.content or [Text("")],
                    theme=theme,
                    render_index=render_index,
                    word_document=word_document,
            )

        if table_block.caption is not None:
            caption = self._add_paragraph(container)
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._append_runs(
                caption,
                self._caption_fragments(theme.table_label, render_index.table_number(table_block), table_block.caption),
                default_size=theme.caption_font_size,
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )

    def _render_figure(
        self,
        container: object,
        figure: Figure,
        theme: Theme,
        render_index: RenderIndex,
        *,
        word_document: WordDocument,
    ) -> None:
        paragraph = self._add_paragraph(container)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        width = Inches(figure.width_inches) if figure.width_inches is not None else None
        run.add_picture(str(figure.image_path), width=width)

        if figure.caption is not None:
            caption = self._add_paragraph(container)
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._append_runs(
                caption,
                self._caption_fragments(theme.figure_label, render_index.figure_number(figure), figure.caption),
                default_size=theme.caption_font_size,
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )

    def _set_paragraph_shading(self, paragraph: object, fill: str) -> None:
        paragraph_properties = paragraph._p.get_or_add_pPr()
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), fill)
        paragraph_properties.append(shading)

    def _set_cell_shading(self, cell: object, fill: str) -> None:
        properties = cell._tc.get_or_add_tcPr()
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), fill)
        properties.append(shading)

    def _set_cell_borders(self, cell: object, color: str, width: float) -> None:
        properties = cell._tc.get_or_add_tcPr()
        borders = OxmlElement("w:tcBorders")
        size = str(max(int(round(width * 8)), 0))
        for edge_name in ("top", "left", "bottom", "right"):
            edge = OxmlElement(f"w:{edge_name}")
            edge.set(qn("w:val"), "single")
            edge.set(qn("w:sz"), size)
            edge.set(qn("w:space"), "0")
            edge.set(qn("w:color"), color)
            borders.append(edge)
        properties.append(borders)

    def _set_cell_padding(self, cell: object, padding: float) -> None:
        properties = cell._tc.get_or_add_tcPr()
        margins = OxmlElement("w:tcMar")
        margin_value = str(max(int(round(padding * 20)), 0))
        for side in ("top", "left", "bottom", "right"):
            element = OxmlElement(f"w:{side}")
            element.set(qn("w:w"), margin_value)
            element.set(qn("w:type"), "dxa")
            margins.append(element)
        properties.append(margins)

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
        word_document: WordDocument,
        title: list[Text] | None,
        entries: list[object],
        theme: Theme,
        render_index: RenderIndex,
        default_title: str,
        label: str,
    ) -> None:
        self._add_heading(word_document, title or [Text(default_title)], level=theme.generated_section_level, theme=theme, number_label=None)
        for entry in entries:
            paragraph = word_document.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.25)
            self._append_runs(
                paragraph,
                self._caption_fragments(label, entry.number, entry.block.caption),
                default_size=theme.caption_font_size,
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )

    def _render_comments_page(
        self,
        word_document: WordDocument,
        title: list[Text] | None,
        theme: Theme,
        render_index: RenderIndex,
    ) -> None:
        word_document.add_page_break()
        self._add_heading(word_document, title or [Text(theme.comments_title)], level=theme.generated_section_level, theme=theme, number_label=None)
        for entry in render_index.comments:
            paragraph = word_document.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.3)
            paragraph.paragraph_format.first_line_indent = Inches(-0.3)
            self._append_runs(
                paragraph,
                [Text(f"[{entry.number}] ")] + entry.comment.comment,
                default_size=theme.body_font_size,
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )

    def _render_references_page(
        self,
        word_document: WordDocument,
        title: list[Text] | None,
        theme: Theme,
        render_index: RenderIndex,
    ) -> None:
        word_document.add_page_break()
        self._add_heading(word_document, title or [Text(theme.references_title)], level=theme.generated_section_level, theme=theme, number_label=None)
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
                word_document=word_document,
            )

    def _render_table_of_contents(
        self,
        word_document: WordDocument,
        title: list[Text] | None,
        theme: Theme,
        render_index: RenderIndex,
    ) -> None:
        self._add_heading(word_document, title or [Text(theme.contents_title)], level=theme.generated_section_level, theme=theme, number_label=None)
        for entry in render_index.headings:
            paragraph = word_document.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.2 * max(entry.level - 1, 0))
            paragraph.paragraph_format.space_after = Pt(3)
            self._append_runs(
                paragraph,
                self._heading_fragments(entry.title, entry.number),
                default_size=theme.body_font_size,
                theme=theme,
                render_index=render_index,
                word_document=word_document,
            )

    def _add_page_number_footer(self, word_document: WordDocument, theme: Theme) -> None:
        for section in word_document.sections:
            footer = section.footer
            paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            paragraph.style = "Footer"
            paragraph.alignment = ALIGNMENTS[theme.page_number_alignment]
            for child in list(paragraph._p):
                if child.tag != qn("w:pPr"):
                    paragraph._p.remove(child)
            parts = theme.page_number_format.split("{page}")
            for index, part in enumerate(parts):
                if part:
                    run = paragraph.add_run(part)
                    self._apply_run_style(run, Text(part).style, default_size=theme.page_number_font_size)
                if index < len(parts) - 1:
                    self._append_page_number_field(paragraph)

    def _append_page_number_field(self, paragraph: object) -> None:
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = "1"
        run.append(text)
        field.append(run)
        paragraph._p.append(field)

    def _comment_marker(self, fragment: Comment, render_index: RenderIndex | None) -> str:
        if render_index is None:
            return "[?]"
        return f"[{render_index.comment_number(fragment)}]"

    def _flatten_fragments(self, fragments: list[Text], theme: Theme | None, render_index: RenderIndex | None) -> str:
        parts: list[str] = []
        for fragment in fragments:
            if isinstance(fragment, Comment):
                parts.append(fragment.value)
                parts.append(self._comment_marker(fragment, render_index))
                continue
            parts.append(self._resolve_fragment_text(fragment, theme, render_index))
        return "".join(parts)
