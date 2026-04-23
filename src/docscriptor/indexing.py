"""Document indexing utilities used by renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from docscriptor.blocks import (
    Block,
    Box,
    BulletList,
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
from docscriptor.document import Document
from docscriptor.inline import Citation, Comment, Footnote, Hyperlink, Text
from docscriptor.references import CitationLibrary, CitationSource
from docscriptor.styles import Theme
from docscriptor.tables import Figure, Table
from docscriptor.core import DocscriptorError


@dataclass(slots=True)
class CitationReferenceEntry:
    """A cited bibliography entry with its assigned reference number."""

    number: int
    source: CitationSource
    anchor: str


@dataclass(slots=True)
class CommentReferenceEntry:
    """A numbered inline comment encountered during indexing."""

    number: int
    comment: Comment


@dataclass(slots=True)
class FootnoteReferenceEntry:
    """A numbered portable footnote encountered during indexing."""

    number: int
    footnote: Footnote


@dataclass(slots=True)
class HeadingEntry:
    """A heading included in the generated table of contents."""

    level: int
    title: list[Text]
    number: str | None = None
    anchor: str | None = None


@dataclass(slots=True)
class CaptionEntry:
    """A numbered caption entry for a table or figure block."""

    number: int
    block: Table | Figure
    anchor: str


@dataclass(slots=True)
class RenderIndex:
    """Numbering and lookup information derived from a document tree."""

    tables: list[CaptionEntry] = field(default_factory=list)
    figures: list[CaptionEntry] = field(default_factory=list)
    table_numbers: dict[int, int] = field(default_factory=dict)
    figure_numbers: dict[int, int] = field(default_factory=dict)
    citations: list[CitationReferenceEntry] = field(default_factory=list)
    citation_numbers: dict[str, int] = field(default_factory=dict)
    citation_source_numbers: dict[int, int] = field(default_factory=dict)
    comments: list[CommentReferenceEntry] = field(default_factory=list)
    comment_numbers: dict[int, int] = field(default_factory=dict)
    footnotes: list[FootnoteReferenceEntry] = field(default_factory=list)
    footnote_numbers: dict[int, int] = field(default_factory=dict)
    headings: list[HeadingEntry] = field(default_factory=list)
    heading_numbers: dict[int, str] = field(default_factory=dict)
    heading_anchors: dict[int, str] = field(default_factory=dict)

    def table_number(self, table: Table) -> int | None:
        """Return the assigned table number for a captioned table."""

        return self.table_numbers.get(id(table))

    def figure_number(self, figure: Figure) -> int | None:
        """Return the assigned figure number for a captioned figure."""

        return self.figure_numbers.get(id(figure))

    def citation_number(self, target: CitationSource | str) -> int:
        """Return the assigned citation number for a source or key."""

        if isinstance(target, CitationSource):
            if target.key is not None and target.key in self.citation_numbers:
                return self.citation_numbers[target.key]
            source_id = id(target)
            if source_id in self.citation_source_numbers:
                return self.citation_source_numbers[source_id]
            raise DocscriptorError(f"Unknown citation source: {target.title!r}")
        if target not in self.citation_numbers:
            raise DocscriptorError(f"Unknown citation key: {target!r}")
        return self.citation_numbers[target]

    def comment_number(self, target: Comment) -> int:
        """Return the assigned inline comment number."""

        if id(target) not in self.comment_numbers:
            raise DocscriptorError(f"Unknown comment target: {target.value!r}")
        return self.comment_numbers[id(target)]

    def footnote_number(self, target: Footnote) -> int:
        """Return the assigned footnote number."""

        if id(target) not in self.footnote_numbers:
            raise DocscriptorError(f"Unknown footnote target: {target.value!r}")
        return self.footnote_numbers[id(target)]

    def heading_number(self, target: Section) -> str | None:
        """Return the numbering label assigned to a section heading."""

        return self.heading_numbers.get(id(target))

    def table_anchor(self, table: Table) -> str | None:
        """Return the bookmark name for a captioned table."""

        number = self.table_number(table)
        if number is None:
            return None
        return f"table_{number}"

    def figure_anchor(self, figure: Figure) -> str | None:
        """Return the bookmark name for a captioned figure."""

        number = self.figure_number(figure)
        if number is None:
            return None
        return f"figure_{number}"

    def citation_anchor(self, target: CitationSource | str) -> str:
        """Return the bookmark name for a cited reference entry."""

        return f"citation_{self.citation_number(target)}"

    def heading_anchor(self, target: Section) -> str | None:
        """Return the bookmark name for a numbered heading."""

        return self.heading_anchors.get(id(target))


def build_render_index(document: Document) -> RenderIndex:
    """Scan a document tree and assign render-time numbering."""

    render_index = RenderIndex()
    _index_blocks(
        document.body.children,
        render_index,
        document.citations,
        document.theme,
        heading_counters=[],
    )
    return render_index


def _advance_heading_counters(counters: list[int], level: int) -> list[int]:
    while len(counters) < level:
        counters.append(0)
    for index in range(max(level - 1, 0)):
        if counters[index] == 0:
            counters[index] = 1
    counters[level - 1] += 1
    del counters[level:]
    return counters


def _index_blocks(
    blocks: Sequence[Block],
    render_index: RenderIndex,
    citations: CitationLibrary,
    theme: Theme,
    *,
    heading_counters: list[int],
) -> None:
    for block in blocks:
        if isinstance(block, Paragraph):
            _index_inlines(block.content, render_index, citations)
            continue
        if isinstance(block, (BulletList, NumberedList)):
            for item in block.items:
                _index_inlines(item.content, render_index, citations)
            continue
        if isinstance(block, Equation):
            continue
        if isinstance(block, Box):
            if block.title is not None:
                _index_inlines(block.title, render_index, citations)
            _index_blocks(
                block.children,
                render_index,
                citations,
                theme,
                heading_counters=heading_counters,
            )
            continue
        if isinstance(block, Section):
            _index_inlines(block.title, render_index, citations)
            current_counters = heading_counters
            number_label: str | None = None
            if block.numbered:
                current_counters = _advance_heading_counters(
                    heading_counters,
                    block.level,
                )
                number_label = theme.format_heading_label(
                    current_counters[: block.level]
                )
                render_index.headings.append(
                    HeadingEntry(
                        level=block.level,
                        title=block.title,
                        number=number_label,
                        anchor=f"heading_{len(render_index.headings) + 1}",
                    )
                )
                render_index.heading_anchors[id(block)] = (
                    render_index.headings[-1].anchor or ""
                )
                if number_label is not None:
                    render_index.heading_numbers[id(block)] = number_label
            _index_blocks(
                block.children,
                render_index,
                citations,
                theme,
                heading_counters=current_counters,
            )
            continue
        if isinstance(
            block,
            (
                TableList,
                FigureList,
                ReferencesPage,
                CommentsPage,
                FootnotesPage,
                TableOfContents,
            ),
        ):
            if block.title is not None:
                _index_inlines(block.title, render_index, citations)
            continue
        if isinstance(block, Table):
            for header_row in block.header_rows:
                for header in header_row:
                    _index_inlines(header.content.content, render_index, citations)
            for row in block.rows:
                for cell in row:
                    _index_inlines(cell.content.content, render_index, citations)
            if block.caption is not None:
                _index_inlines(block.caption.content, render_index, citations)
                number = len(render_index.tables) + 1
                render_index.tables.append(
                    CaptionEntry(
                        number=number,
                        block=block,
                        anchor=f"table_{number}",
                    )
                )
                render_index.table_numbers[id(block)] = number
            continue
        if isinstance(block, Figure):
            if block.caption is not None:
                _index_inlines(block.caption.content, render_index, citations)
                number = len(render_index.figures) + 1
                render_index.figures.append(
                    CaptionEntry(
                        number=number,
                        block=block,
                        anchor=f"figure_{number}",
                    )
                )
                render_index.figure_numbers[id(block)] = number


def _index_inlines(
    fragments: Sequence[Text],
    render_index: RenderIndex,
    citations: CitationLibrary,
) -> None:
    for fragment in fragments:
        if isinstance(fragment, Hyperlink):
            _index_inlines(fragment.label, render_index, citations)
            continue
        if isinstance(fragment, Comment):
            _index_inlines(fragment.comment, render_index, citations)
            if id(fragment) in render_index.comment_numbers:
                continue
            number = len(render_index.comments) + 1
            render_index.comments.append(
                CommentReferenceEntry(number=number, comment=fragment)
            )
            render_index.comment_numbers[id(fragment)] = number
            continue
        if isinstance(fragment, Footnote):
            _index_inlines(fragment.note, render_index, citations)
            if id(fragment) in render_index.footnote_numbers:
                continue
            number = len(render_index.footnotes) + 1
            render_index.footnotes.append(
                FootnoteReferenceEntry(number=number, footnote=fragment)
            )
            render_index.footnote_numbers[id(fragment)] = number
            continue
        if isinstance(fragment, Citation):
            target = fragment.target
            if isinstance(target, CitationSource):
                if target.key is not None and target.key in render_index.citation_numbers:
                    continue
                if id(target) in render_index.citation_source_numbers:
                    continue
                source = target
            else:
                if target in render_index.citation_numbers:
                    continue
                source = citations.resolve(target)

            number = len(render_index.citations) + 1
            render_index.citations.append(
                CitationReferenceEntry(
                    number=number,
                    source=source,
                    anchor=f"citation_{number}",
                )
            )
            render_index.citation_source_numbers[id(source)] = number
            if source.key is not None:
                render_index.citation_numbers[source.key] = number
