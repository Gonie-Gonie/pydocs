from __future__ import annotations

import importlib.util
from html import unescape
from io import BytesIO
from pathlib import Path
import re

from docx import Document as WordDocument
from pypdf import PdfReader


def _load_example_module(example_dir: str):
    module_path = Path(__file__).resolve().parents[1] / "examples" / example_dir / "main.py"
    spec = importlib.util.spec_from_file_location(f"examples.{example_dir}.main", module_path)
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


def _normalized_html_text(html_path: Path) -> str:
    html_text = html_path.read_text(encoding="utf-8")
    html_text = re.sub(r"<style.*?>.*?</style>", " ", html_text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html_text)
    return " ".join(unescape(text).split())


def test_usage_guide_example_builds_outputs(tmp_path: Path) -> None:
    usage_guide = _load_example_module("usage_guide_example")
    docx_path, pdf_path = usage_guide.build_usage_guide(tmp_path)
    html_path = tmp_path / "docscriptor-usage-guide.html"

    assert docx_path.exists()
    assert pdf_path.exists()
    assert html_path.exists()
    assert (Path(usage_guide.__file__).resolve().parent / "assets" / "usage-guide-figure.png").exists()

    word_document = WordDocument(docx_path)
    paragraph_texts = [paragraph.text for paragraph in word_document.paragraphs]
    table_text = "\n".join(
        cell.text
        for table in word_document.tables
        for row in table.rows
        for cell in row.cells
    )
    pdf_reader = PdfReader(BytesIO(pdf_path.read_bytes()))
    pdf_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)

    assert "Using docscriptor" in paragraph_texts
    assert "List of Tables" in paragraph_texts
    assert "List of Figures" in paragraph_texts
    assert "Contents" in paragraph_texts
    assert "Footnotes" in paragraph_texts
    assert "Comments" in paragraph_texts
    assert "References" in paragraph_texts
    assert "1 Getting Started" in paragraph_texts
    assert "1.1 What docscriptor is" in paragraph_texts
    assert "1.2 Quick Start" in paragraph_texts
    assert "2 Document Model" in paragraph_texts
    assert "2.1 Structural objects" in paragraph_texts
    assert "2.2 Inline actions" in paragraph_texts
    assert "2.3 Generated pages" in paragraph_texts
    assert "3 Layout and Styling" in paragraph_texts
    assert "3.2 Heading and list numbering" in paragraph_texts
    assert "3.3 Boxes and grouped content" in paragraph_texts
    assert "4 Tables and Figures" in paragraph_texts
    assert "4.1 Tables" in paragraph_texts
    assert "4.2 Figures" in paragraph_texts
    assert "5 Notes and References" in paragraph_texts
    assert "6 Project Layout" in paragraph_texts
    assert "7 End-to-End Workflow" in paragraph_texts
    assert any("bold(...)" in text for text in paragraph_texts)
    assert any("Text.from_markup(...)" in text for text in paragraph_texts)
    assert any("The repository itself can be cited directly as [1]" in text for text in paragraph_texts)
    assert any("generated comments page" in text for text in paragraph_texts)
    assert any("Portable footnotes stay stable" in text for text in paragraph_texts)
    assert any("This footnote was created from a table cell inside the usage guide." in text for text in paragraph_texts)
    assert any("dx = (" in text and ")/(3)" in text for text in paragraph_texts)
    assert any("This usage guide is intentionally assembled in one main.py file." in text for text in paragraph_texts)
    assert any("The smallest useful workflow is: import the classes you need" in text for text in paragraph_texts)
    assert "Detailed usage guide and API walkthrough" in paragraph_texts
    assert "docscriptor examples" in paragraph_texts
    assert any("Python-first document authoring toolkit" in text for text in paragraph_texts)
    assert "Grouped Content Example" in table_text
    assert any("examples/journal_paper_example/main.py" in text for text in paragraph_texts)
    assert 'w:instr="PAGE"' in word_document.sections[0].footer.paragraphs[0]._p.xml
    assert len(word_document.tables) == 6
    assert len(word_document.inline_shapes) == 2
    assert paragraph_texts.count("Table 1. Rendering goals and output formats.") >= 2
    assert paragraph_texts.count("Table 2. Core authoring objects by responsibility.") >= 2
    assert paragraph_texts.count("Table 3. Generated pages available in a document.") >= 2
    assert paragraph_texts.count("Table 4. Default numbering behavior and customization hooks.") >= 2
    assert paragraph_texts.count("Table 5. Table layout options from simple headers to merged spans.") >= 2
    assert paragraph_texts.count("Figure 1. Example figure loaded directly from the example asset directory.") >= 2

    assert "Using docscriptor" in pdf_text
    assert "List of Tables" in pdf_text
    assert "List of Figures" in pdf_text
    assert "Contents" in pdf_text
    assert "Footnotes" in pdf_text
    assert "Comments" in pdf_text
    assert "References" in pdf_text
    assert "Getting Started" in pdf_text
    assert "Document Model" in pdf_text
    assert "Quick Start" in pdf_text
    assert "Structural objects" in pdf_text
    assert "Inline actions" in pdf_text
    assert "Generated pages" in pdf_text
    assert "Boxes and grouped content" in pdf_text
    assert "Project Layout" in pdf_text
    assert "End-to-End Workflow" in pdf_text
    assert "The repository itself can be cited directly as [1]" in pdf_text
    assert "Portable footnotes stay stable" in pdf_text
    assert "bold(...)" in pdf_text
    assert "Text.from_markup(...)" in pdf_text
    assert "colored accents" in pdf_text
    assert "Literate Programming" in pdf_text
    assert "https://github.com/Gonie-Gonie/pydocs" in pdf_text
    assert "This footnote was created from a table cell inside the usage guide." in pdf_text
    assert "examples/journal_paper_example/main.py" in pdf_text
    assert len(pdf_reader.pages) >= 10
    assert _pdf_image_draw_count(pdf_path) == 2

    html_text = html_path.read_text(encoding="utf-8")
    normalized_html_text = _normalized_html_text(html_path)
    assert "Using docscriptor" in normalized_html_text
    assert "List of Tables" in normalized_html_text
    assert "List of Figures" in normalized_html_text
    assert "Contents" in normalized_html_text
    assert "Footnotes" in normalized_html_text
    assert "Comments" in normalized_html_text
    assert "References" in normalized_html_text
    assert "1 Getting Started" in normalized_html_text
    assert "2 Document Model" in normalized_html_text
    assert "3 Layout and Styling" in normalized_html_text
    assert "4 Tables and Figures" in normalized_html_text
    assert "5 Notes and References" in normalized_html_text
    assert "6 Project Layout" in normalized_html_text
    assert "7 End-to-End Workflow" in normalized_html_text
    assert "save_html(...)" in normalized_html_text
    assert "The same document tree can render to DOCX, PDF, and HTML." in normalized_html_text
    assert "Portable footnotes stay stable in DOCX, PDF, and HTML" in normalized_html_text
    assert "https://github.com/Gonie-Gonie/pydocs" in normalized_html_text
    assert "examples/journal_paper_example/main.py" in normalized_html_text
    assert html_text.count("data:image/png;base64,") == 2
    assert 'href="#table_1"' in html_text
    assert 'href="#figure_1"' in html_text
