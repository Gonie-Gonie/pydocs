from __future__ import annotations

import importlib.util
from io import BytesIO
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


def _pdf_image_draw_count(pdf_path: Path) -> int:
    count = 0
    for page in PdfReader(BytesIO(pdf_path.read_bytes())).pages:
        resources = page.get("/Resources")
        if resources is None or "/XObject" not in resources:
            continue
        xobjects = resources["/XObject"].get_object()
        image_names = {
            name
            for name, xobject in xobjects.items()
            if xobject.get_object().get("/Subtype") == "/Image"
        }
        if not image_names:
            continue
        content = page.get_contents()
        if content is None:
            continue
        content_bytes = content.get_data()
        for name in image_names:
            token = f"{name} Do".encode()
            count += content_bytes.count(token)
    return count


def _pdf_content_bytes(pdf_path: Path) -> bytes:
    parts: list[bytes] = []
    for page in PdfReader(BytesIO(pdf_path.read_bytes())).pages:
        contents = page.get_contents()
        if contents is None:
            continue
        if isinstance(contents, list):
            for item in contents:
                parts.append(item.get_data())
        else:
            parts.append(contents.get_data())
    return b"\n".join(parts)


def _pdf_text_context(pdf_path: Path, text: str, window: int = 160) -> bytes:
    content = _pdf_content_bytes(pdf_path)
    needle = f"({text})".encode()
    index = content.find(needle)
    assert index != -1, f"{text!r} not found in PDF content stream"
    start = max(index - window, 0)
    return content[start : index + len(needle) + window]


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
    assert "Contents" in paragraph_texts
    assert "List of Tables" in paragraph_texts
    assert "List of Figures" in paragraph_texts
    assert "References" in paragraph_texts
    assert any("The default theme uses Times New Roman body text" in text for text in paragraph_texts)
    assert any("See Table 1 for the core block inventory and Figure 1" in text for text in paragraph_texts)
    assert any("Use Figure 2 together with Table 2" in text for text in paragraph_texts)
    assert any("The project repository itself can be cited inline, as shown by [1]." in text for text in paragraph_texts)
    assert any("literate-programming tradition described in [2]" in text for text in paragraph_texts)
    assert any("from docscriptor import Chapter, Document, Paragraph, Section" in text for text in paragraph_texts)
    assert any("class WarningParagraph(Paragraph):" in text for text in paragraph_texts)
    assert any(paragraph.style.name == "List Bullet" for paragraph in word_document.paragraphs)
    assert any(paragraph.style.name == "List Number" for paragraph in word_document.paragraphs)
    assert len(word_document.inline_shapes) == 2
    assert len(word_document.tables) == 2
    assert word_document.tables[0].cell(2, 1).text == "Paragraph, BulletList, NumberedList, CodeBlock, Table, Figure"
    assert word_document.tables[1].cell(1, 0).text == "Editable review"
    assert word_document.tables[1].cell(2, 1).text == "PDF"
    assert paragraph_texts.count("Table 1. Core authoring primitives.") >= 2
    assert paragraph_texts.count("Table 2. Rendering outputs by goal.") >= 2
    assert paragraph_texts.count("Figure 1. Heading hierarchy example output.") >= 2
    assert paragraph_texts.count("Figure 2. Repeated figure rendering example.") >= 2
    assert any("https://github.com/Gonie-Gonie/pydocs" in text for text in paragraph_texts)
    assert any("Literate Programming" in text for text in paragraph_texts)
    assert any("https://doi.org/10.1093/comjnl/27.2.97" in text for text in paragraph_texts)
    assert word_document.styles["Normal"].font.name == "Times New Roman"
    assert paragraph_texts.index("List of Tables") < paragraph_texts.index("List of Figures")
    assert paragraph_texts.index("List of Figures") < paragraph_texts.index("Contents")
    assert paragraph_texts.index("Contents") < paragraph_texts.index("Getting Started")
    heading_styles = {paragraph.text: paragraph.style.name for paragraph in word_document.paragraphs if paragraph.text in {"List of Tables", "List of Figures", "References"}}
    assert heading_styles["List of Tables"] == "Heading 2"
    assert heading_styles["List of Figures"] == "Heading 2"
    assert heading_styles["References"] == "Heading 2"

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_path.read_bytes())).pages)
    assert "Using docscriptor" in pdf_text
    assert "Getting Started" in pdf_text
    assert "Core Building Blocks" in pdf_text
    assert "Hierarchy Depth" in pdf_text
    assert "When To Use CodeBlock" in pdf_text
    assert "Generated Lists" in pdf_text
    assert "Contents" in pdf_text
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
    assert "literate-programming tradition described in [2]" in pdf_text
    assert "from docscriptor import Chapter, Document, Paragraph, Section" in pdf_text
    assert "class WarningParagraph(Paragraph):" in pdf_text
    assert "https://github.com/Gonie-Gonie/pydocs" in pdf_text
    assert "Literate Programming" in pdf_text
    assert "https://doi.org/10.1093/comjnl/27.2.97" in pdf_text
    assert _pdf_image_draw_count(pdf_path) == 2
    assert pdf_text.index("List of Tables") < pdf_text.index("List of Figures")
    assert pdf_text.index("List of Figures") < pdf_text.index("Contents")
    assert pdf_text.index("Contents") < pdf_text.index("Getting Started")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "Contents")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "List of Tables")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "List of Figures")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "References")
