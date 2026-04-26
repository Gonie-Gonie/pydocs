"""Top-level package for docscriptor."""

from docscriptor.components.blocks import (
    Box,
    BulletList,
    Chapter,
    CodeBlock,
    Equation,
    NumberedList,
    Paragraph,
    Section,
    Subsection,
    Subsubsection,
)
from docscriptor.components.generated import CommentsPage, FigureList, ReferencesPage, TableList, TableOfContents
from docscriptor.components.media import Figure, Table, TableCell
from docscriptor.document import Document
from docscriptor.core import DocscriptorError
from docscriptor.components.inline import (
    Comment,
    Footnote,
    Math,
    Text,
    bold,
    code,
    color,
    cite,
    comment,
    footnote,
    italic,
    link,
    math,
    styled,
)
from docscriptor.markup import md, markup
from docscriptor.references import CitationLibrary, CitationSource
from docscriptor.settings import (
    BoxStyle,
    DocumentSettings,
    HeadingNumbering,
    ListStyle,
    ParagraphStyle,
    TableStyle,
    TextStyle,
    Theme,
)

__version__ = "0.2.0"

__all__ = [
    "Box",
    "BoxStyle",
    "BulletList",
    "CitationLibrary",
    "CitationSource",
    "Chapter",
    "Comment",
    "CommentsPage",
    "CodeBlock",
    "Document",
    "DocumentSettings",
    "DocscriptorError",
    "Equation",
    "Figure",
    "FigureList",
    "Footnote",
    "HeadingNumbering",
    "ListStyle",
    "Math",
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
    "bold",
    "code",
    "color",
    "cite",
    "comment",
    "footnote",
    "italic",
    "link",
    "math",
    "md",
    "markup",
    "styled",
]

for _module_name in ("components", "core", "document", "references", "settings"):
    globals().pop(_module_name, None)

del _module_name
