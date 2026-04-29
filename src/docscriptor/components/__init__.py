"""Grouped component namespaces for more granular imports."""

from __future__ import annotations

from importlib import import_module


_EXPORTS = {
    "Affiliation": "docscriptor.components.people",
    "Author": "docscriptor.components.people",
    "AuthorLayout": "docscriptor.components.people",
    "Bold": "docscriptor.components.inline",
    "Box": "docscriptor.components.blocks",
    "BulletList": "docscriptor.components.blocks",
    "Chapter": "docscriptor.components.blocks",
    "Citation": "docscriptor.components.inline",
    "CitationLibrary": "docscriptor.components.references",
    "CitationSource": "docscriptor.components.references",
    "CodeBlock": "docscriptor.components.blocks",
    "Comment": "docscriptor.components.inline",
    "CommentsPage": "docscriptor.components.generated",
    "Equation": "docscriptor.components.blocks",
    "Figure": "docscriptor.components.media",
    "FigureList": "docscriptor.components.generated",
    "Footnote": "docscriptor.components.inline",
    "FootnotesPage": "docscriptor.components.generated",
    "Hyperlink": "docscriptor.components.inline",
    "ImageBox": "docscriptor.components.sheets",
    "Italic": "docscriptor.components.inline",
    "Math": "docscriptor.components.inline",
    "Monospace": "docscriptor.components.inline",
    "NumberedList": "docscriptor.components.blocks",
    "Paragraph": "docscriptor.components.blocks",
    "ReferencesPage": "docscriptor.components.generated",
    "Section": "docscriptor.components.blocks",
    "Shape": "docscriptor.components.sheets",
    "Sheet": "docscriptor.components.sheets",
    "Subsection": "docscriptor.components.blocks",
    "Subsubsection": "docscriptor.components.blocks",
    "Table": "docscriptor.components.media",
    "TableCell": "docscriptor.components.media",
    "TableList": "docscriptor.components.generated",
    "TableOfContents": "docscriptor.components.generated",
    "Text": "docscriptor.components.inline",
    "TextBox": "docscriptor.components.sheets",
    "bold": "docscriptor.components.inline",
    "code": "docscriptor.components.inline",
    "color": "docscriptor.components.inline",
    "cite": "docscriptor.components.inline",
    "comment": "docscriptor.components.inline",
    "footnote": "docscriptor.components.inline",
    "italic": "docscriptor.components.inline",
    "link": "docscriptor.components.inline",
    "math": "docscriptor.components.inline",
    "md": "docscriptor.components.markup",
    "markup": "docscriptor.components.markup",
    "styled": "docscriptor.components.inline",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
