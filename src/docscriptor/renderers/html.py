"""HTML renderer."""

from __future__ import annotations

from base64 import b64encode
from html import escape
from io import BytesIO
from mimetypes import guess_type
from pathlib import Path

from docscriptor.blocks import (
    Box,
    BulletList,
    CodeBlock,
    CommentsPage,
    Equation,
    FigureList,
    FootnotesPage,
    NumberedList,
    Paragraph,
    ReferencesPage,
    Section,
    TableList,
    TableOfContents,
)
from docscriptor.core import DocscriptorError, PathLike
from docscriptor.document import Document
from docscriptor.equations import SUBSCRIPT, SUPERSCRIPT, parse_latex_segments
from docscriptor.indexing import RenderIndex, build_render_index
from docscriptor.inline import (
    _BlockReference,
    Citation,
    Comment,
    Footnote,
    Hyperlink,
    Math,
    Text,
)
from docscriptor.renderers.context import HtmlRenderContext
from docscriptor.styles import ParagraphStyle, Theme
from docscriptor.tables import Figure, Table, TablePlacement, build_table_layout


class HtmlRenderer:
    """Render docscriptor documents into standalone HTML files."""

    def render(self, document: Document, output_path: PathLike) -> Path:
        """Render a docscriptor document to an HTML file."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        render_index = build_render_index(document)
        context = HtmlRenderContext(
            theme=document.theme,
            render_index=render_index,
        )
        front_children, main_children = document.split_top_level_children()
        has_front_matter = document.cover_page or bool(front_children)

        body_parts = [
            '<div class="docscriptor-document">',
            self._render_title_matter(
                document,
                context,
                page_break_after=document.cover_page and (bool(front_children) or bool(main_children)),
            ),
        ]

        if has_front_matter:
            if front_children:
                body_parts.append(
                    '<section class="docscriptor-front-matter">'
                    + self._render_children(front_children, context)
                    + "</section>"
                )
            if main_children:
                body_parts.append(
                    '<section class="docscriptor-main-matter docscriptor-page-break-before">'
                    + self._render_children(main_children, context)
                    + "</section>"
                )
        else:
            body_parts.append(
                '<section class="docscriptor-main-matter">'
                + self._render_children(main_children, context)
                + "</section>"
            )

        body_parts.append("</div>")

        html = "\n".join(
            [
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8" />',
                '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
                f"  <title>{escape(document.title)}</title>",
                f"  <meta name=\"description\" content=\"{escape(document.summary or document.title)}\" />",
                "  <style>",
                self._stylesheet(document.theme),
                "  </style>",
                "</head>",
                "<body>",
                *body_parts,
                "</body>",
                "</html>",
            ]
        )
        path.write_text(html, encoding="utf-8")
        return path

    def render_paragraph(self, block: Paragraph, context: HtmlRenderContext) -> str:
        """Render a paragraph block into HTML."""

        return (
            f'<p class="docscriptor-paragraph" style="{self._paragraph_style_css(block.style, context.theme)}">'
            + self._inline_html(
                block.content,
                context.theme,
                context.render_index,
            )
            + "</p>"
        )

    def render_list(
        self,
        block: BulletList | NumberedList,
        context: HtmlRenderContext,
    ) -> str:
        """Render a list block into HTML."""

        list_style = block.style or context.theme.list_style(
            ordered=isinstance(block, NumberedList)
        )
        items = []
        for index, item in enumerate(block.items):
            marker = escape(list_style.marker_for(index))
            items.append(
                (
                    '<div class="docscriptor-list-item" '
                    f'style="column-gap: {list_style.marker_gap:.2f}in; padding-left: {list_style.indent:.2f}in;">'
                    f'<div class="docscriptor-list-marker">{marker}</div>'
                    '<div class="docscriptor-list-content">'
                    f'<p class="docscriptor-paragraph" style="{self._paragraph_style_css(item.style, context.theme, default_space_after=3.0)}">'
                    + self._inline_html(
                        item.content,
                        context.theme,
                        context.render_index,
                    )
                    + "</p>"
                    "</div>"
                    "</div>"
                )
            )
        list_class = "docscriptor-numbered-list" if isinstance(block, NumberedList) else "docscriptor-bullet-list"
        return f'<div class="docscriptor-list {list_class}">{"".join(items)}</div>'

    def render_code_block(
        self,
        block: CodeBlock,
        context: HtmlRenderContext,
    ) -> str:
        """Render a code block into HTML."""

        label = (
            f'<div class="docscriptor-code-language">{escape(block.language.upper())}</div>'
            if block.language
            else ""
        )
        return (
            '<section class="docscriptor-code-block">'
            + label
            + f'<pre class="docscriptor-code" style="margin-bottom: {(block.style.space_after or 0):.1f}pt;">'
            + escape(block.code)
            + "</pre>"
            + "</section>"
        )

    def render_equation(
        self,
        block: Equation,
        context: HtmlRenderContext,
    ) -> str:
        """Render a block equation into HTML."""

        line_height = block.style.leading or max(context.theme.body_font_size + 1, 12) * 1.3
        return (
            '<div class="docscriptor-equation" '
            f'style="text-align: {block.style.alignment}; margin: 0 0 {(block.style.space_after or 0):.1f}pt; line-height: {line_height:.1f}pt;">'
            + self._math_html(
                Math(block.expression),
                context.theme,
                base_size=max(context.theme.body_font_size + 1, 12),
            )
            + "</div>"
        )

    def render_box(self, block: Box, context: HtmlRenderContext) -> str:
        """Render a box and its children into HTML."""

        self._assert_box_children_supported(block.children)
        title_html = ""
        if block.title is not None:
            title_html = (
                '<div class="docscriptor-box-title" '
                f'style="{self._box_title_css(block, context.theme)}">'
                + self._inline_html(
                    block.title,
                    context.theme,
                    context.render_index,
                    base_bold=True,
                )
                + "</div>"
            )
        children_html = "".join(
            child.render_to_html(self, context)
            for child in block.children
        )
        return (
            '<section class="docscriptor-box" '
            f'style="{self._box_css(block)}">'
            + title_html
            + children_html
            + "</section>"
        )

    def render_section(self, block: Section, context: HtmlRenderContext) -> str:
        """Render a titled section and its children into HTML."""

        heading_tag = self._heading_tag(block.level)
        number_label = context.render_index.heading_number(block) if block.numbered else None
        anchor = context.render_index.heading_anchor(block) if block.numbered else None
        children_html = "".join(
            child.render_to_html(self, context)
            for child in block.children
        )
        heading_html = (
            f"<{heading_tag}"
            + (f' id="{escape(anchor)}"' if anchor else "")
            + f' class="docscriptor-heading docscriptor-heading-level-{block.level}"'
            + f' style="{self._heading_css(block.level, context.theme)}">'
            + self._inline_html(
                self._heading_fragments(block.title, number_label),
                context.theme,
                context.render_index,
                base_bold=context.theme.heading_emphasis(block.level)[0],
                base_italic=context.theme.heading_emphasis(block.level)[1],
                base_size=context.theme.heading_size(block.level),
            )
            + f"</{heading_tag}>"
        )
        return (
            f'<section class="docscriptor-section docscriptor-section-level-{block.level}">'
            + heading_html
            + children_html
            + "</section>"
        )

    def render_table(self, block: Table, context: HtmlRenderContext) -> str:
        """Render a table block into HTML."""

        layout = build_table_layout(block.header_rows, block.rows)
        colgroup = ""
        if block.column_widths is not None:
            columns = "".join(
                f'<col style="width: {width:.2f}in;" />'
                for width in block.column_widths
            )
            colgroup = f"<colgroup>{columns}</colgroup>"

        thead_html = self._table_section_html(
            layout,
            header=True,
            block=block,
            context=context,
        )
        tbody_html = self._table_section_html(
            layout,
            header=False,
            block=block,
            context=context,
        )
        caption_html = (
            self._caption_html(
                block.caption,
                label=context.theme.table_label,
                number=context.render_index.table_number(block),
                anchor=context.render_index.table_anchor(block),
                context=context,
                kind="table",
            )
            if block.caption is not None
            else ""
        )
        table_html = (
            '<div class="docscriptor-table-wrapper">'
            + (
                caption_html
                if block.caption is not None and context.theme.table_caption_position == "above"
                else ""
            )
            + '<table class="docscriptor-table">'
            + colgroup
            + (f"<thead>{thead_html}</thead>" if thead_html else "")
            + (f"<tbody>{tbody_html}</tbody>" if tbody_html else "")
            + "</table>"
            + (
                caption_html
                if block.caption is not None and context.theme.table_caption_position == "below"
                else ""
            )
            + "</div>"
        )
        return table_html

    def render_figure(self, block: Figure, context: HtmlRenderContext) -> str:
        """Render a figure block into HTML."""

        image_style = ""
        if block.width_inches is not None:
            image_style = f' style="max-width: {block.width_inches:.2f}in; width: 100%;"'
        image_html = (
            f'<img class="docscriptor-figure-image" src="{self._figure_src(block)}" '
            f'alt="{escape(block.caption.plain_text() if block.caption is not None else "Figure")}"{image_style} />'
        )
        caption_html = (
            self._caption_html(
                block.caption,
                label=context.theme.figure_label,
                number=context.render_index.figure_number(block),
                anchor=context.render_index.figure_anchor(block),
                context=context,
                kind="figure",
            )
            if block.caption is not None
            else ""
        )
        content_parts = []
        if block.caption is not None and context.theme.figure_caption_position == "above":
            content_parts.append(caption_html)
        content_parts.append(image_html)
        if block.caption is not None and context.theme.figure_caption_position == "below":
            content_parts.append(caption_html)
        return '<figure class="docscriptor-figure">' + "".join(content_parts) + "</figure>"

    def render_table_list(
        self,
        block: TableList,
        context: HtmlRenderContext,
    ) -> str:
        """Render the generated list of tables into HTML."""

        return self._render_caption_list(
            title=block.title,
            entries=context.render_index.tables,
            default_title=context.theme.list_of_tables_title,
            label=context.theme.table_label,
            context=context,
            section_class="docscriptor-generated-page docscriptor-table-list",
        )

    def render_figure_list(
        self,
        block: FigureList,
        context: HtmlRenderContext,
    ) -> str:
        """Render the generated list of figures into HTML."""

        return self._render_caption_list(
            title=block.title,
            entries=context.render_index.figures,
            default_title=context.theme.list_of_figures_title,
            label=context.theme.figure_label,
            context=context,
            section_class="docscriptor-generated-page docscriptor-figure-list",
        )

    def render_comments_page(
        self,
        block: CommentsPage,
        context: HtmlRenderContext,
    ) -> str:
        """Render the generated comments page into HTML."""

        entries = "".join(
            (
                f'<p class="docscriptor-generated-entry" id="comment_{entry.number}">'
                f'<span class="docscriptor-generated-marker">[{entry.number}]</span> '
                + self._inline_html(
                    entry.comment.comment,
                    context.theme,
                    context.render_index,
                )
                + "</p>"
            )
            for entry in context.render_index.comments
        )
        return self._generated_page_html(
            title=block.title or [Text(context.theme.comments_title)],
            body=entries,
            context=context,
            section_class="docscriptor-generated-page docscriptor-comments-page",
        )

    def render_footnotes_page(
        self,
        block: FootnotesPage,
        context: HtmlRenderContext,
    ) -> str:
        """Render the generated footnotes page into HTML."""

        entries = "".join(
            (
                f'<p class="docscriptor-generated-entry" id="footnote_{entry.number}">'
                f'<span class="docscriptor-generated-marker">[{entry.number}]</span> '
                + self._inline_html(
                    entry.footnote.note,
                    context.theme,
                    context.render_index,
                )
                + "</p>"
            )
            for entry in context.render_index.footnotes
        )
        return self._generated_page_html(
            title=block.title or [Text(context.theme.footnotes_title)],
            body=entries,
            context=context,
            section_class="docscriptor-generated-page docscriptor-footnotes-page",
        )

    def render_references_page(
        self,
        block: ReferencesPage,
        context: HtmlRenderContext,
    ) -> str:
        """Render the generated references page into HTML."""

        entries = "".join(
            (
                f'<p class="docscriptor-generated-entry" id="{escape(entry.anchor)}">'
                f'<span class="docscriptor-generated-marker">[{entry.number}]</span> '
                + self._inline_html(
                    entry.source.reference_fragments(),
                    context.theme,
                    context.render_index,
                )
                + "</p>"
            )
            for entry in context.render_index.citations
        )
        return self._generated_page_html(
            title=block.title or [Text(context.theme.references_title)],
            body=entries,
            context=context,
            section_class="docscriptor-generated-page docscriptor-references-page",
        )

    def render_table_of_contents(
        self,
        block: TableOfContents,
        context: HtmlRenderContext,
    ) -> str:
        """Render the generated table of contents into HTML."""

        entries = "".join(
            (
                '<div class="docscriptor-toc-entry" '
                f'style="margin-left: {max(entry.level - 1, 0) * 18:.1f}px;'
                + (" font-weight: 700;" if entry.level == 1 else "")
                + (' margin-top: 4px;' if entry.level == 1 else "")
                + '">'
                + self._link_html(
                    entry.anchor,
                    self._inline_html(
                        self._heading_fragments(entry.title, entry.number),
                        context.theme,
                        context.render_index,
                    ),
                    internal=True,
                )
                + "</div>"
            )
            for entry in context.render_index.headings
        )
        return self._generated_page_html(
            title=block.title or [Text(context.theme.contents_title)],
            body='<nav class="docscriptor-toc">' + entries + "</nav>",
            context=context,
            section_class="docscriptor-generated-page docscriptor-toc-page",
        )

    def _render_children(
        self,
        children: list[object],
        context: HtmlRenderContext,
    ) -> str:
        return "".join(child.render_to_html(self, context) for child in children)

    def _render_title_matter(
        self,
        document: Document,
        context: HtmlRenderContext,
        *,
        page_break_after: bool,
    ) -> str:
        classes = ["docscriptor-title-matter"]
        if document.cover_page:
            classes.append("docscriptor-cover-page")
        if page_break_after:
            classes.append("docscriptor-page-break-after")

        lines = [
            self._title_line_html(
                [Text(document.title)],
                font_size=context.theme.title_font_size,
                alignment=context.theme.title_alignment,
                bold=True,
                class_name="docscriptor-title",
                theme=context.theme,
            )
        ]
        if document.subtitle is not None:
            lines.append(
                self._title_line_html(
                    document.subtitle,
                    font_size=max(context.theme.body_font_size + 1, 12),
                    alignment=context.theme.subtitle_alignment,
                    italic=True,
                    class_name="docscriptor-subtitle",
                    theme=context.theme,
                )
            )
        for author_line in document.authors:
            lines.append(
                self._title_line_html(
                    author_line,
                    font_size=context.theme.body_font_size,
                    alignment=context.theme.author_alignment,
                    class_name="docscriptor-author",
                    theme=context.theme,
                )
            )
        for affiliation_line in document.affiliations:
            lines.append(
                self._title_line_html(
                    affiliation_line,
                    font_size=max(context.theme.body_font_size - 0.5, 9),
                    alignment=context.theme.affiliation_alignment,
                    italic=True,
                    class_name="docscriptor-affiliation",
                    theme=context.theme,
                )
            )
        return f'<header class="{" ".join(classes)}">{"".join(lines)}</header>'

    def _title_line_html(
        self,
        fragments: list[Text],
        *,
        font_size: float,
        alignment: str,
        class_name: str,
        theme: Theme,
        bold: bool = False,
        italic: bool = False,
    ) -> str:
        tag = "h1" if class_name == "docscriptor-title" else "p"
        return (
            f'<{tag} class="{class_name}" style="text-align: {alignment}; font-size: {font_size:.1f}pt;">'
            + self._inline_html(
                fragments,
                theme,
                RenderIndex(),
                base_bold=bold,
                base_italic=italic,
                base_size=font_size,
            )
            + f"</{tag}>"
        )

    def _render_caption_list(
        self,
        *,
        title: list[Text] | None,
        entries: list[object],
        default_title: str,
        label: str,
        context: HtmlRenderContext,
        section_class: str,
    ) -> str:
        items = "".join(
            (
                '<div class="docscriptor-caption-list-entry">'
                + self._link_html(
                    entry.anchor,
                    self._inline_html(
                        self._caption_fragments(
                            label,
                            entry.number,
                            entry.block.caption,
                        ),
                        context.theme,
                        context.render_index,
                    ),
                    internal=True,
                )
                + "</div>"
            )
            for entry in entries
        )
        return self._generated_page_html(
            title=title or [Text(default_title)],
            body=items,
            context=context,
            section_class=section_class,
        )

    def _generated_page_html(
        self,
        *,
        title: list[Text],
        body: str,
        context: HtmlRenderContext,
        section_class: str,
    ) -> str:
        level = context.theme.generated_section_level
        heading_tag = self._heading_tag(level)
        heading_html = (
            f"<{heading_tag} class=\"docscriptor-generated-title\" style=\"{self._heading_css(level, context.theme)}\">"
            + self._inline_html(
                title,
                context.theme,
                context.render_index,
                base_bold=context.theme.heading_emphasis(level)[0],
                base_italic=context.theme.heading_emphasis(level)[1],
                base_size=context.theme.heading_size(level),
            )
            + f"</{heading_tag}>"
        )
        return f'<section class="{section_class}">{heading_html}{body}</section>'

    def _table_section_html(
        self,
        layout: object,
        *,
        header: bool,
        block: Table,
        context: HtmlRenderContext,
    ) -> str:
        rows: dict[int, list[TablePlacement]] = {}
        for placement in layout.placements:
            if placement.header != header:
                continue
            rows.setdefault(placement.row, []).append(placement)
        html_rows: list[str] = []
        tag = "th" if header else "td"
        for row_index in sorted(rows):
            cells = []
            for placement in sorted(rows[row_index], key=lambda value: value.column):
                cells.append(self._table_cell_html(placement, tag, block, context))
            html_rows.append("<tr>" + "".join(cells) + "</tr>")
        return "".join(html_rows)

    def _table_cell_html(
        self,
        placement: TablePlacement,
        tag: str,
        block: Table,
        context: HtmlRenderContext,
    ) -> str:
        style_parts = [
            f"border: 1px solid #{block.style.border_color}",
            "vertical-align: top",
            f"padding: {block.style.cell_padding:.1f}pt",
        ]
        if placement.header:
            style_parts.append(f"background: #{block.style.header_background_color}")
            style_parts.append(f"color: #{block.style.header_text_color}")
            style_parts.append("font-weight: 700")
        else:
            background_color = placement.cell.background_color
            if (
                background_color is None
                and block.style.alternate_row_background_color is not None
                and placement.body_row_index is not None
                and placement.body_row_index % 2 == 1
            ):
                background_color = block.style.alternate_row_background_color
            if background_color is None:
                background_color = block.style.body_background_color
            if background_color is not None:
                style_parts.append(f"background: #{background_color}")
        attrs = []
        if placement.cell.colspan > 1:
            attrs.append(f' colspan="{placement.cell.colspan}"')
        if placement.cell.rowspan > 1:
            attrs.append(f' rowspan="{placement.cell.rowspan}"')
        return (
            f"<{tag}{''.join(attrs)} style=\"{'; '.join(style_parts)}\">"
            + self.render_paragraph(
                placement.cell.content,
                HtmlRenderContext(
                    theme=context.theme,
                    render_index=context.render_index,
                ),
            )
            + f"</{tag}>"
        )

    def _caption_html(
        self,
        caption: Paragraph | None,
        *,
        label: str,
        number: int | None,
        anchor: str | None,
        context: HtmlRenderContext,
        kind: str,
    ) -> str:
        if caption is None:
            return ""
        tag = "figcaption" if kind == "figure" else "div"
        anchor_attr = f' id="{escape(anchor)}"' if anchor else ""
        return (
            f"<{tag}{anchor_attr} class=\"docscriptor-caption docscriptor-{kind}-caption\" "
            f'style="text-align: {context.theme.caption_alignment}; font-size: {context.theme.caption_size():.1f}pt;">'
            + self._inline_html(
                self._caption_fragments(label, number, caption),
                context.theme,
                context.render_index,
                base_size=context.theme.caption_size(),
            )
            + f"</{tag}>"
        )

    def _inline_html(
        self,
        fragments: list[Text],
        theme: Theme,
        render_index: RenderIndex,
        *,
        base_bold: bool = False,
        base_italic: bool = False,
        base_size: float | None = None,
    ) -> str:
        return "".join(
            self._fragment_html(
                fragment,
                theme,
                render_index,
                base_bold=base_bold,
                base_italic=base_italic,
                base_size=base_size,
            )
            for fragment in fragments
        ) or "&nbsp;"

    def _fragment_html(
        self,
        fragment: Text,
        theme: Theme,
        render_index: RenderIndex,
        *,
        base_bold: bool,
        base_italic: bool,
        base_size: float | None,
    ) -> str:
        if isinstance(fragment, Hyperlink):
            return self._link_html(
                fragment.target,
                self._inline_html(
                    fragment.label,
                    theme,
                    render_index,
                    base_size=base_size,
                ),
                internal=fragment.internal,
            )
        if isinstance(fragment, _BlockReference):
            return self._link_html(
                self._block_reference_anchor(fragment.target, render_index),
                self._styled_text_html(
                    self._resolve_block_reference(fragment.target, theme, render_index),
                    fragment,
                    theme,
                    base_bold=base_bold,
                    base_italic=base_italic,
                    base_size=base_size,
                ),
                internal=True,
            )
        if isinstance(fragment, Citation):
            citation_number = render_index.citation_number(fragment.target)
            return self._link_html(
                f"citation_{citation_number}",
                self._styled_text_html(
                    f"[{citation_number}]",
                    fragment,
                    theme,
                    base_bold=base_bold,
                    base_italic=base_italic,
                    base_size=base_size,
                ),
                internal=True,
            )
        if isinstance(fragment, Comment):
            comment_number = render_index.comment_number(fragment)
            visible = self._styled_text_html(
                fragment.value,
                fragment,
                theme,
                base_bold=base_bold,
                base_italic=base_italic,
                base_size=base_size,
            )
            marker = self._link_html(
                f"comment_{comment_number}",
                f"[{comment_number}]",
                internal=True,
            )
            return f"{visible}<sup>{marker}</sup>"
        if isinstance(fragment, Footnote):
            footnote_number = render_index.footnote_number(fragment)
            visible = self._styled_text_html(
                fragment.value,
                fragment,
                theme,
                base_bold=base_bold,
                base_italic=base_italic,
                base_size=base_size,
            )
            marker = self._link_html(
                f"footnote_{footnote_number}",
                str(footnote_number),
                internal=True,
            )
            return f"{visible}<sup>{marker}</sup>"
        if isinstance(fragment, Math):
            return self._math_html(
                fragment,
                theme,
                base_bold=base_bold,
                base_italic=base_italic,
                base_size=base_size,
            )
        return self._styled_text_html(
            self._resolve_fragment_text(fragment, theme, render_index),
            fragment,
            theme,
            base_bold=base_bold,
            base_italic=base_italic,
            base_size=base_size,
        )

    def _styled_text_html(
        self,
        text_value: str,
        fragment: Text,
        theme: Theme,
        *,
        base_bold: bool = False,
        base_italic: bool = False,
        base_size: float | None = None,
    ) -> str:
        text = escape(text_value).replace("\n", "<br/>")
        styles: list[str] = []
        effective_bold = base_bold if fragment.style.bold is None else fragment.style.bold
        effective_italic = base_italic if fragment.style.italic is None else fragment.style.italic
        if fragment.style.font_name is not None:
            styles.append(f"font-family: {self._css_font_family(fragment.style.font_name)}")
        if fragment.style.font_size is not None and fragment.style.font_size != base_size:
            styles.append(f"font-size: {fragment.style.font_size:.1f}pt")
        if effective_bold != base_bold:
            styles.append(f"font-weight: {'700' if effective_bold else '400'}")
        if effective_italic != base_italic:
            styles.append(f"font-style: {'italic' if effective_italic else 'normal'}")
        if fragment.style.underline:
            styles.append("text-decoration: underline")
        if fragment.style.color is not None:
            styles.append(f"color: #{fragment.style.color}")
        if not styles:
            return text
        return f'<span style="{"; ".join(styles)}">{text}</span>'

    def _math_html(
        self,
        fragment: Math,
        theme: Theme,
        *,
        base_bold: bool = False,
        base_italic: bool = False,
        base_size: float | None = None,
    ) -> str:
        parts: list[str] = []
        for segment in parse_latex_segments(fragment.value):
            piece = self._styled_text_html(
                segment.text,
                fragment,
                theme,
                base_bold=base_bold,
                base_italic=base_italic,
                base_size=base_size,
            )
            if segment.vertical_align == SUPERSCRIPT:
                piece = f"<sup>{piece}</sup>"
            elif segment.vertical_align == SUBSCRIPT:
                piece = f"<sub>{piece}</sub>"
            parts.append(piece)
        return '<span class="docscriptor-math">' + ("".join(parts) or "&nbsp;") + "</span>"

    def _resolve_fragment_text(
        self,
        fragment: Text,
        theme: Theme,
        render_index: RenderIndex,
    ) -> str:
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

    def _resolve_block_reference(
        self,
        target: Table | Figure,
        theme: Theme,
        render_index: RenderIndex,
    ) -> str:
        if isinstance(target, Table):
            number = render_index.table_number(target)
            if number is None:
                raise DocscriptorError(
                    "Table references require the target table to have a caption and be included in the document"
                )
            return f"{theme.table_label} {number}"

        number = render_index.figure_number(target)
        if number is None:
            raise DocscriptorError(
                "Figure references require the target figure to have a caption and be included in the document"
            )
        return f"{theme.figure_label} {number}"

    def _block_reference_anchor(
        self,
        target: Table | Figure,
        render_index: RenderIndex,
    ) -> str | None:
        if isinstance(target, Table):
            return render_index.table_anchor(target)
        return render_index.figure_anchor(target)

    def _figure_src(self, figure: Figure) -> str:
        source = figure.image_source
        if isinstance(source, Path):
            image_bytes = source.read_bytes()
            mime_type = guess_type(source.name)[0] or self._mime_type_for_format(source.suffix.lstrip(".") or figure.format)
        elif hasattr(source, "savefig"):
            buffer = BytesIO()
            save_kwargs: dict[str, object] = {"format": figure.format}
            if figure.dpi is not None:
                save_kwargs["dpi"] = figure.dpi
            source.savefig(buffer, **save_kwargs)
            image_bytes = buffer.getvalue()
            mime_type = self._mime_type_for_format(figure.format)
        else:
            raise TypeError(f"Unsupported figure source for HTML rendering: {type(source)!r}")
        return f"data:{mime_type};base64,{b64encode(image_bytes).decode('ascii')}"

    def _mime_type_for_format(self, image_format: str) -> str:
        normalized = image_format.strip().lower()
        if normalized in {"jpg", "jpeg"}:
            return "image/jpeg"
        if normalized == "svg":
            return "image/svg+xml"
        return f"image/{normalized or 'png'}"

    def _caption_fragments(
        self,
        label: str,
        number: int | None,
        caption: Paragraph,
    ) -> list[Text]:
        if number is None:
            return caption.content
        return [Text(f"{label} {number}. ")] + caption.content

    def _heading_fragments(
        self,
        title: list[Text],
        number_label: str | None,
    ) -> list[Text]:
        if not number_label:
            return title
        return [Text(f"{number_label} ")] + title

    def _heading_tag(self, level: int) -> str:
        return f"h{min(level + 1, 6)}"

    def _heading_css(self, level: int, theme: Theme) -> str:
        bold, italic = theme.heading_emphasis(level)
        styles = [
            f"font-size: {theme.heading_size(level):.1f}pt",
            f"text-align: {theme.heading_alignment(level)}",
            f"margin: {'18' if level == 1 else '12'}pt 0 {'10' if level == 1 else '6'}pt",
        ]
        if bold:
            styles.append("font-weight: 700")
        if italic:
            styles.append("font-style: italic")
        return "; ".join(styles)

    def _paragraph_style_css(
        self,
        style: ParagraphStyle,
        theme: Theme,
        *,
        default_space_after: float | None = None,
    ) -> str:
        space_after = style.space_after
        if space_after is None:
            space_after = default_space_after if default_space_after is not None else 0
        line_height = style.leading or theme.body_font_size * 1.35
        return (
            f"text-align: {style.alignment};"
            f" margin: 0 0 {space_after:.1f}pt;"
            f" line-height: {line_height:.1f}pt;"
        )

    def _box_css(self, block: Box) -> str:
        return (
            f"border: {block.style.border_width:.2f}pt solid #{block.style.border_color};"
            f" background: #{block.style.background_color};"
            f" padding: {block.style.padding:.1f}pt;"
            f" margin: 0 0 {block.style.space_after:.1f}pt;"
        )

    def _box_title_css(self, block: Box, theme: Theme) -> str:
        parts = [
            "font-weight: 700",
            "margin: 0 0 6pt",
        ]
        if block.style.title_background_color is not None:
            parts.append(f"background: #{block.style.title_background_color}")
            parts.append("padding: 4pt 6pt")
        parts.append(f"font-size: {theme.body_font_size:.1f}pt")
        return "; ".join(parts)

    def _assert_box_children_supported(self, children: list[object]) -> None:
        unsupported = (
            CommentsPage,
            FootnotesPage,
            ReferencesPage,
            TableOfContents,
            TableList,
            FigureList,
        )
        for child in children:
            if isinstance(child, unsupported):
                raise DocscriptorError(f"{type(child).__name__} cannot be rendered inside a Box")

    def _link_html(
        self,
        target: str | None,
        inner_html: str,
        *,
        internal: bool = False,
    ) -> str:
        if not target:
            return inner_html
        href = f"#{target}" if internal else target
        return f'<a href="{escape(href)}">{inner_html}</a>'

    def _css_font_family(self, font_name: str) -> str:
        fallback = "monospace" if "courier" in font_name.lower() else "serif" if "times" in font_name.lower() else "sans-serif"
        escaped_name = font_name.replace('"', '\\"')
        return f'"{escaped_name}", {fallback}'

    def _stylesheet(self, theme: Theme) -> str:
        page_break_before = (
            "break-before: page; page-break-before: always;"
            if theme.generated_page_breaks
            else ""
        )
        return f"""
:root {{
  color-scheme: light;
}}
body {{
  margin: 0;
  background: linear-gradient(180deg, #f3f0e8 0%, #ece6da 100%);
  color: #1e2329;
  font-family: {self._css_font_family(theme.body_font_name)};
  font-size: {theme.body_font_size:.1f}pt;
}}
.docscriptor-document {{
  max-width: 8.5in;
  margin: 0 auto;
  padding: 32px 24px 48px;
}}
.docscriptor-title-matter,
.docscriptor-front-matter,
.docscriptor-main-matter,
.docscriptor-generated-page,
.docscriptor-box,
.docscriptor-table-wrapper,
.docscriptor-figure {{
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 40px rgba(60, 48, 28, 0.08);
  border-radius: 16px;
}}
.docscriptor-title-matter,
.docscriptor-front-matter,
.docscriptor-main-matter,
.docscriptor-generated-page {{
  padding: 24px 26px;
  margin-bottom: 18px;
}}
.docscriptor-cover-page {{
  min-height: 40vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.docscriptor-page-break-after {{
  break-after: page;
  page-break-after: always;
}}
.docscriptor-page-break-before {{
  {page_break_before}
}}
.docscriptor-title {{
  margin: 0 0 12pt;
}}
.docscriptor-subtitle,
.docscriptor-author,
.docscriptor-affiliation {{
  margin-top: 0;
}}
.docscriptor-paragraph {{
  font-family: {self._css_font_family(theme.body_font_name)};
}}
.docscriptor-list {{
  margin: 0 0 10pt;
}}
.docscriptor-list-item {{
  display: grid;
  grid-template-columns: max-content 1fr;
  align-items: start;
}}
.docscriptor-list-marker {{
  text-align: right;
  padding-top: 1px;
  white-space: pre-wrap;
}}
.docscriptor-list-content > .docscriptor-paragraph {{
  margin-top: 0;
}}
.docscriptor-code-block {{
  margin: 0 0 12pt;
}}
.docscriptor-code-language {{
  font-family: {self._css_font_family(theme.monospace_font_name)};
  font-size: {theme.caption_size():.1f}pt;
  font-weight: 700;
  margin-bottom: 2pt;
}}
.docscriptor-code {{
  margin-top: 0;
  overflow-x: auto;
  padding: 10pt 12pt;
  border: 0.75pt solid #d8e0eb;
  background: #f5f7fa;
  border-radius: 12px;
  font-family: {self._css_font_family(theme.monospace_font_name)};
  font-size: {max(theme.body_font_size - 1, 8):.1f}pt;
  line-height: {max(theme.body_font_size - 1, 8) * 1.35:.1f}pt;
}}
.docscriptor-equation {{
  font-size: {max(theme.body_font_size + 1, 12):.1f}pt;
}}
.docscriptor-box {{
  overflow: hidden;
}}
.docscriptor-table-wrapper {{
  padding: 14px 16px;
  margin: 0 0 12pt;
}}
.docscriptor-table {{
  width: 100%;
  border-collapse: collapse;
}}
.docscriptor-table .docscriptor-paragraph {{
  margin-bottom: 0;
}}
.docscriptor-caption {{
  margin: 6pt 0;
}}
.docscriptor-figure {{
  margin: 0 0 12pt;
  padding: 16px;
  text-align: center;
}}
.docscriptor-figure-image {{
  display: inline-block;
  max-width: 100%;
  height: auto;
}}
.docscriptor-generated-title {{
  margin-top: 0;
}}
.docscriptor-generated-entry,
.docscriptor-caption-list-entry,
.docscriptor-toc-entry {{
  margin: 0 0 6pt;
}}
.docscriptor-generated-marker {{
  font-weight: 700;
}}
.docscriptor-math {{
  letter-spacing: 0.01em;
}}
a {{
  color: #0c5d78;
  text-decoration: underline;
  text-underline-offset: 0.08em;
}}
@media (max-width: 860px) {{
  .docscriptor-document {{
    padding: 16px 12px 24px;
  }}
  .docscriptor-title-matter,
  .docscriptor-front-matter,
  .docscriptor-main-matter,
  .docscriptor-generated-page,
  .docscriptor-table-wrapper,
  .docscriptor-figure {{
    padding: 18px 16px;
    border-radius: 12px;
  }}
}}
""".strip()
