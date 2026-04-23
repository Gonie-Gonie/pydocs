from __future__ import annotations

import importlib.util
from io import BytesIO
from pathlib import Path

import docscriptor
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


def _docx_table_texts(word_document: WordDocument) -> list[str]:
    texts: list[str] = []
    for table in word_document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    texts.append(cell.text)
    return texts


def test_usage_guide_example_builds_outputs(tmp_path: Path) -> None:
    usage_guide = _load_usage_guide_module()
    docx_path, pdf_path = usage_guide.build_usage_guide(tmp_path)

    assert docx_path.exists()
    assert pdf_path.exists()
    assert (tmp_path / "usage-guide-figure.png").exists()

    word_document = WordDocument(docx_path)
    paragraph_texts = [paragraph.text for paragraph in word_document.paragraphs]
    table_texts = _docx_table_texts(word_document)
    docx_text = "\n".join(paragraph_texts + table_texts)
    compact_docx_text = "".join(docx_text.split())
    assert "Using docscriptor" in paragraph_texts
    assert "1 Getting Started" in paragraph_texts
    assert "1 Authoring Model" in paragraph_texts
    assert "1 API Reference" in paragraph_texts
    assert "1.1 Quick Start" in paragraph_texts
    assert "1.1.1 Hierarchy Depth" in paragraph_texts
    assert "1.1.1.1 When To Use CodeBlock" in paragraph_texts
    assert "1.1 Reusable Abstractions" in paragraph_texts
    assert "1.1 Generated Lists" in paragraph_texts
    assert "1.1 Document and Structure" in paragraph_texts
    assert "1.1 Blocks and Generated Pages" in paragraph_texts
    assert "1.1 Text, Style, and Theme" in paragraph_texts
    assert "1.1 Citations, Helpers, and Errors" in paragraph_texts
    assert "1.1 Public Methods" in paragraph_texts
    assert "Comments" in paragraph_texts
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
    assert any("every stable name exported from docscriptor" in text for text in paragraph_texts)
    assert any("__version__ exposes the package version string" in text for text in paragraph_texts)
    assert any("Body," in text for text in paragraph_texts)
    assert any("Portable comments such as review note[1]" in text for text in paragraph_texts)
    assert any("inline math such as" in text and "2 + " in text and " = " in text for text in paragraph_texts)
    assert any("dx = (" in text and ")/(3)" in text for text in paragraph_texts)
    assert any(text == "1. Import the model objects you need." for text in paragraph_texts)
    assert any(text == "• Show a complete example without losing indentation." for text in paragraph_texts)
    assert 'w:instr="PAGE"' in word_document.sections[0].footer.paragraphs[0]._p.xml
    assert word_document.sections[0].footer.paragraphs[0].text.startswith("Page ")
    assert len(word_document.inline_shapes) == 2
    assert len(word_document.tables) == 8
    assert word_document.tables[0].cell(2, 1).text == "Paragraph, BulletList, NumberedList, CodeBlock, Equation, Table, Figure"
    assert word_document.tables[1].cell(1, 0).text == "Editable review"
    assert word_document.tables[1].cell(2, 1).text == "PDF"
    assert word_document.tables[2].cell(1, 0).text == "Document"
    assert word_document.tables[3].cell(5, 0).text == "Box"
    assert word_document.tables[5].cell(9, 0).text == "BoxStyle"
    assert word_document.tables[5].cell(10, 0).text == "HeadingNumbering"
    assert word_document.tables[5].cell(11, 0).text == "ListStyle"
    assert word_document.tables[6].cell(7, 0).text == "__version__"
    assert word_document.tables[7].cell(1, 0).text == "Document.save_docx(path)"
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
    assert paragraph_texts.index("Contents") < paragraph_texts.index("1 Getting Started")
    heading_styles = {paragraph.text: paragraph.style.name for paragraph in word_document.paragraphs if paragraph.text in {"Comments", "List of Tables", "List of Figures", "References"}}
    assert heading_styles["Comments"] == "Heading 2"
    assert heading_styles["List of Tables"] == "Heading 2"
    assert heading_styles["List of Figures"] == "Heading 2"
    assert heading_styles["References"] == "Heading 2"
    for public_name in docscriptor.__all__:
        assert public_name in compact_docx_text
    for method_name in (
        "save_docx",
        "save_pdf",
        "plain_text",
        "plain_title",
        "merged",
        "format_label",
        "marker_for",
        "heading_size",
        "heading_emphasis",
        "heading_alignment",
        "format_heading_label",
        "list_style",
        "format_page_number",
        "format_reference",
        "resolve",
        "from_bibtex",
        "add",
    ):
        assert method_name in compact_docx_text

    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_path.read_bytes())).pages)
    normalized_pdf_text = " ".join(pdf_text.split())
    compact_pdf_text = "".join(pdf_text.split())
    assert "Using docscriptor" in pdf_text
    assert "Getting Started" in pdf_text
    assert "Core Building Blocks" in pdf_text
    assert "Hierarchy Depth" in pdf_text
    assert "When To Use CodeBlock" in pdf_text
    assert "Generated Lists" in pdf_text
    assert "API Reference" in pdf_text
    assert "Document and Structure" in pdf_text
    assert "Blocks and Generated Pages" in pdf_text
    assert "Text, Style, and Theme" in pdf_text
    assert "Citations, Helpers, and Errors" in pdf_text
    assert "Public Methods" in pdf_text
    assert "Comments" in pdf_text
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
    assert "every stable name exported from docscriptor" in normalized_pdf_text
    assert "__version__ exposes the package version string" in normalized_pdf_text
    assert "Body" in pdf_text
    assert "Portable comments such as review note[1]" in pdf_text
    assert "inline math such as" in pdf_text
    assert "dx = (" in pdf_text
    assert "Page 1" in pdf_text
    assert "https://github.com/Gonie-Gonie/pydocs" in pdf_text
    assert "Literate Programming" in pdf_text
    assert "https://doi.org/10.1093/comjnl/27.2.97" in pdf_text
    assert _pdf_image_draw_count(pdf_path) == 2
    assert pdf_text.index("List of Tables") < pdf_text.index("List of Figures")
    assert pdf_text.index("List of Figures") < pdf_text.index("Contents")
    assert pdf_text.index("Contents") < pdf_text.index("Getting Started")
    assert "1 Getting Started" in pdf_text
    assert "1.1 Quick Start" in pdf_text
    assert "1.1.1 Hierarchy Depth" in pdf_text
    assert "1.1.1.1 When To Use CodeBlock" in pdf_text
    assert "HeadingNumbering" in pdf_text
    assert "ListStyle" in pdf_text
    assert "BoxStyle" in pdf_text
    assert b"15 Tf" in _pdf_text_context(pdf_path, "Contents")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "List of Tables")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "List of Figures")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "Comments")
    assert b"15 Tf" in _pdf_text_context(pdf_path, "References")
    for public_name in docscriptor.__all__:
        assert public_name in compact_pdf_text
    for method_name in (
        "save_docx",
        "save_pdf",
        "plain_text",
        "plain_title",
        "merged",
        "format_label",
        "marker_for",
        "heading_size",
        "heading_emphasis",
        "heading_alignment",
        "format_heading_label",
        "list_style",
        "format_page_number",
        "format_reference",
        "resolve",
        "from_bibtex",
        "add",
    ):
        assert method_name in compact_pdf_text
