from __future__ import annotations

import importlib.util
from pathlib import Path

from docx import Document as WordDocument
from pypdf import PdfReader


def _load_usage_guide_module():
    module_path = Path(__file__).resolve().parents[1] / "examples" / "usage_guide.py"
    spec = importlib.util.spec_from_file_location("examples.usage_guide", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_usage_guide_example_builds_outputs(tmp_path: Path) -> None:
    usage_guide = _load_usage_guide_module()
    docx_path, pdf_path = usage_guide.build_usage_guide(tmp_path)

    assert docx_path.exists()
    assert pdf_path.exists()
    assert (tmp_path / "usage-guide-figure.png").exists()

    word_document = WordDocument(docx_path)
    paragraph_texts = [paragraph.text for paragraph in word_document.paragraphs]
    assert "Using docscriptor" in paragraph_texts
    assert "Getting Started" in paragraph_texts
    assert "Authoring Model" in paragraph_texts
    assert "Quick Start" in paragraph_texts
    assert "Hierarchy Depth" in paragraph_texts
    assert "When To Use CodeBlock" in paragraph_texts
    assert "Reusable Abstractions" in paragraph_texts
    assert "Generated Lists" in paragraph_texts
    assert "List of Tables" in paragraph_texts
    assert "List of Figures" in paragraph_texts
    assert "References" in paragraph_texts
    assert any("The default theme uses Times New Roman body text" in text for text in paragraph_texts)
    assert any("See Table 1 for the core block inventory and Figure 1" in text for text in paragraph_texts)
    assert any("Use Figure 2 together with Table 2" in text for text in paragraph_texts)
    assert any("The project repository itself can be cited inline, as shown by [1]." in text for text in paragraph_texts)
    assert any("from docscriptor import Chapter, Document, Paragraph, Section" in text for text in paragraph_texts)
    assert any("class WarningParagraph(Paragraph):" in text for text in paragraph_texts)
    assert any(paragraph.style.name == "List Bullet" for paragraph in word_document.paragraphs)
    assert any(paragraph.style.name == "List Number" for paragraph in word_document.paragraphs)
    assert len(word_document.tables) == 2
    assert word_document.tables[0].cell(2, 1).text == "Paragraph, BulletList, NumberedList, CodeBlock, Table, Figure"
    assert word_document.tables[1].cell(1, 0).text == "Editable review"
    assert word_document.tables[1].cell(2, 1).text == "PDF"
    assert paragraph_texts.count("Table 1. Core authoring primitives.") >= 2
    assert paragraph_texts.count("Table 2. Rendering outputs by goal.") >= 2
    assert paragraph_texts.count("Figure 1. Heading hierarchy example output.") >= 2
    assert paragraph_texts.count("Figure 2. Repeated figure rendering example.") >= 2
    assert any("https://github.com/Gonie-Gonie/pydocs" in text for text in paragraph_texts)
    assert word_document.styles["Normal"].font.name == "Times New Roman"

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Using docscriptor" in pdf_text
    assert "Getting Started" in pdf_text
    assert "Core Building Blocks" in pdf_text
    assert "Hierarchy Depth" in pdf_text
    assert "When To Use CodeBlock" in pdf_text
    assert "Generated Lists" in pdf_text
    assert "List of Tables" in pdf_text
    assert "List of Figures" in pdf_text
    assert "References" in pdf_text
    assert pdf_text.count("Table 1. Core authoring primitives.") >= 2
    assert pdf_text.count("Table 2. Rendering outputs by goal.") >= 2
    assert pdf_text.count("Figure 1. Heading hierarchy example output.") >= 2
    assert pdf_text.count("Figure 2. Repeated figure rendering example.") >= 2
    assert "BulletList" in pdf_text
    assert "NumberedList" in pdf_text
    assert "CodeBlock" in pdf_text
    assert "The default theme uses Times New Roman body text" in pdf_text
    assert "See Table 1 for the core block inventory and Figure 1" in pdf_text
    assert "Use Figure 2 together with Table 2" in pdf_text
    assert "The project repository itself can be cited inline, as shown by [1]." in pdf_text
    assert "from docscriptor import Chapter, Document, Paragraph, Section" in pdf_text
    assert "class WarningParagraph(Paragraph):" in pdf_text
    assert "https://github.com/Gonie-Gonie/pydocs" in pdf_text
