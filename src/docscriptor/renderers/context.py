"""Renderer context objects shared with block-level render dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from docscriptor.indexing import RenderIndex
from docscriptor.styles import Theme


@dataclass(slots=True)
class DocxRenderContext:
    """Context needed while rendering blocks into DOCX."""

    theme: Theme
    render_index: RenderIndex
    word_document: Any


@dataclass(slots=True)
class PdfRenderContext:
    """Context needed while rendering blocks into PDF."""

    theme: Theme
    render_index: RenderIndex
    styles: Any
