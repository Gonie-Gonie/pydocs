"""Compatibility re-export layer for the public document model.

The concrete definitions now live in smaller modules such as
``docscriptor.blocks``, ``docscriptor.inline``, ``docscriptor.tables``, and
``docscriptor.document``. This module preserves the long-standing
``docscriptor.model`` import path.
"""

from docscriptor.blocks import (
    Block,
    BlockInput,
    Body,
    Box,
    BulletList,
    CellInput,
    Chapter,
    CodeBlock,
    CommentsPage,
    Equation,
    FigureList,
    FootnotesPage,
    ListInput,
    NumberedList,
    Paragraph,
    ReferencesPage,
    Section,
    Subsection,
    Subsubsection,
    TableList,
    TableOfContents,
    coerce_blocks,
    coerce_cell,
    coerce_list_item,
)
from docscriptor.core import DocscriptorError, PathLike, format_counter_value
from docscriptor.document import Document
from docscriptor.indexing import (
    CaptionEntry,
    CitationReferenceEntry,
    CommentReferenceEntry,
    FootnoteReferenceEntry,
    HeadingEntry,
    RenderIndex,
    build_render_index,
)
from docscriptor.inline import (
    BlockReference,
    Bold,
    Citation,
    Code,
    Comment,
    Emphasis,
    Footnote,
    Hyperlink,
    InlineInput,
    Italic,
    Math,
    Monospace,
    Strong,
    Text,
    _BlockReference,
    bold,
    code,
    color,
    cite,
    coerce_inlines,
    comment,
    footnote,
    italic,
    link,
    math,
    styled,
)
from docscriptor.references import CitationLibrary, CitationSource
from docscriptor.settings import DocumentSettings
from docscriptor.styles import (
    BoxStyle,
    HeadingNumbering,
    ListStyle,
    ParagraphStyle,
    TableStyle,
    TextStyle,
    Theme,
)
from docscriptor.tables import (
    Figure,
    Table,
    TableCell,
    TableCellInput,
    TableLayout,
    TablePlacement,
    build_table_layout,
    coerce_table_cell,
)
