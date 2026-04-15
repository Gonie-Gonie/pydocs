from __future__ import annotations

from pathlib import Path

from docx import Document as WordDocument
from pypdf import PdfReader

from examples.showcase import build_showcase


def test_showcase_script_builds_outputs(tmp_path: Path) -> None:
    docx_path, pdf_path = build_showcase(tmp_path)

    assert docx_path.exists()
    assert pdf_path.exists()
    assert (tmp_path / "showcase-image.png").exists()

    word_document = WordDocument(docx_path)
    paragraph_texts = [paragraph.text for paragraph in word_document.paragraphs]
    assert "Docscriptor Showcase" in paragraph_texts
    assert "Feature Checklist" in paragraph_texts
    assert any(paragraph.style.name == "List Bullet" for paragraph in word_document.paragraphs)
    assert any(paragraph.style.name == "List Number" for paragraph in word_document.paragraphs)
    assert any("Generated placeholder image." in text for text in paragraph_texts)

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Docscriptor Showcase" in pdf_text
    assert "Authoring Model" in pdf_text
    assert "Current showcase capabilities." in pdf_text
    assert "Sections and subsections are regular Python instances." in pdf_text
