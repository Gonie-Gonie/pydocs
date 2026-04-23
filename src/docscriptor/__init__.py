"""Top-level package for docscriptor."""

from docscriptor.blocks import (
    Body,
    Box,
    BulletList,
    Chapter,
    CodeBlock,
    CommentsPage,
    Equation,
    FigureList,
    FootnotesPage,
    NumberedList,
    Paragraph,
    ReferencesPage,
    Section,
    Subsection,
    Subsubsection,
    TableList,
    TableOfContents,
)
from docscriptor.document import Document
from docscriptor.core import DocscriptorError
from docscriptor.inline import (
    Bold,
    Comment,
    Footnote,
    Italic,
    Math,
    Monospace,
    Text,
    cite,
    comment,
    footnote,
    math,
    styled,
)
from docscriptor.markup import md, markup
from docscriptor.references import CitationLibrary, CitationSource
from docscriptor.styles import (
    BoxStyle,
    HeadingNumbering,
    ListStyle,
    ParagraphStyle,
    TableStyle,
    TextStyle,
    Theme,
)
from docscriptor.tables import Figure, Table, TableCell

__version__ = "0.2.0"

__all__ = [
    "Bold",
    "Box",
    "BoxStyle",
    "Body",
    "BulletList",
    "CitationLibrary",
    "CitationSource",
    "Chapter",
    "Comment",
    "CommentsPage",
    "CodeBlock",
    "Document",
    "DocscriptorError",
    "Equation",
    "Figure",
    "FigureList",
    "Footnote",
    "FootnotesPage",
    "HeadingNumbering",
    "Italic",
    "ListStyle",
    "Math",
    "Monospace",
    "NumberedList",
    "Paragraph",
    "ParagraphStyle",
    "ReferencesPage",
    "Section",
    "Subsection",
    "Subsubsection",
    "Table",
    "TableCell",
    "TableStyle",
    "TableOfContents",
    "TableList",
    "Text",
    "TextStyle",
    "Theme",
    "__version__",
    "cite",
    "comment",
    "footnote",
    "math",
    "md",
    "markup",
    "styled",
]

for _module_name in ("blocks", "core", "document", "inline", "references", "styles", "tables"):
    globals().pop(_module_name, None)

del _module_name
