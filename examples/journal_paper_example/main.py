"""Standalone journal paper example for docscriptor."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

from docscriptor import (
    BulletList,
    CitationLibrary,
    CitationSource,
    Document,
    Figure,
    Paragraph,
    ReferencesPage,
    Section,
    Table,
    TableStyle,
    Theme,
    code,
    italic,
)

matplotlib.use("Agg")

import matplotlib.pyplot as plt


OUTPUT_DIR = Path("artifacts") / "journal-paper"
EXAMPLE_DIR = Path(__file__).resolve().parent
ASSET_DIR = EXAMPLE_DIR / "assets"
SYSTEM_DIAGRAM_PATH = ASSET_DIR / "system-diagram.png"
RESULTS_CSV_PATH = ASSET_DIR / "benchmark_results.csv"
ABLATION_CSV_PATH = ASSET_DIR / "ablation_results.csv"


def build_performance_figure(results_df: pd.DataFrame):
    """Create a matplotlib figure directly from the benchmark CSV data."""

    figure, axes = plt.subplots(1, 2, figsize=(7.0, 3.1))

    axes[0].bar(results_df["Model"], results_df["Accuracy"], color="#4C78A8")
    axes[0].set_title("Accuracy")
    axes[0].set_ylabel("Score")
    axes[0].set_ylim(0.84, 0.96)
    axes[0].tick_params(axis="x", rotation=18)

    axes[1].plot(
        results_df["Model"],
        results_df["Latency_ms"],
        marker="o",
        linewidth=2,
        color="#F58518",
    )
    axes[1].set_title("Latency")
    axes[1].set_ylabel("ms")
    axes[1].tick_params(axis="x", rotation=18)

    figure.tight_layout()
    return figure


def build_ablation_figure(ablation_df: pd.DataFrame):
    """Create a matplotlib figure from the ablation CSV data."""

    figure, axis = plt.subplots(figsize=(6.2, 3.0))
    axis.barh(ablation_df["Setting"], ablation_df["Accuracy"], color="#54A24B")
    axis.set_xlabel("Accuracy")
    axis.set_xlim(0.88, 0.95)
    axis.set_title("Ablation Accuracy")
    figure.tight_layout()
    return figure


def build_journal_paper_document() -> Document:
    """Build an example journal-style manuscript."""

    results_df = pd.read_csv(RESULTS_CSV_PATH)
    ablation_df = pd.read_csv(ABLATION_CSV_PATH)
    dataset_df = pd.DataFrame(
        [
            ["Training", 18420, "system logs + editorial metadata"],
            ["Validation", 2400, "held-out internal documents"],
            ["Test", 2600, "final blind review split"],
        ],
        columns=["Split", "Documents", "Source"],
    )

    manuscript_sources = CitationLibrary(
        [
            CitationSource(
                "Literate Programming",
                key="literate-programming",
                authors=("D. E. Knuth",),
                publisher="The Computer Journal",
                year="1984",
                url="https://doi.org/10.1093/comjnl/27.2.97",
            ),
            CitationSource(
                "Statistical Analyses and Reproducible Research",
                key="reproducible-research",
                authors=("Robert Gentleman", "Duncan Temple Lang"),
                publisher="Journal of Computational and Graphical Statistics",
                year="2007",
                url="https://doi.org/10.1198/106186007X178663",
            ),
            CitationSource(
                "knitr: A General-Purpose Package for Dynamic Report Generation in R",
                key="knitr",
                authors=("Yihui Xie",),
                publisher="Official project site",
                year="2026",
                url="https://yihui.org/knitr/",
            ),
        ]
    )

    benchmark_table = Table.from_dataframe(
        results_df[["Model", "Accuracy", "F1", "Latency_ms"]],
        caption="Benchmark results loaded directly from the experiment CSV file.",
        column_widths=[1.8, 1.1, 0.9, 1.2],
        style=TableStyle(
            header_background_color="#DCE8F4",
            alternate_row_background_color="#F7FAFD",
        ),
    )
    ablation_table = Table.from_dataframe(
        ablation_df,
        caption="Ablation results for major document-pipeline design decisions.",
        column_widths=[2.6, 1.0, 1.2],
        style=TableStyle(
            header_background_color="#E3ECF6",
            alternate_row_background_color="#F8FBFD",
        ),
    )
    dataset_table = Table.from_dataframe(
        dataset_df,
        caption="Corpus summary used for the manuscript automation study.",
        column_widths=[1.2, 1.2, 3.0],
        style=TableStyle(
            header_background_color="#E7EEF7",
            alternate_row_background_color="#FAFCFE",
        ),
    )
    system_diagram = Figure(
        SYSTEM_DIAGRAM_PATH,
        caption=Paragraph(
            "System overview diagram stored under the example asset directory."
        ),
        width_inches=5.2,
    )
    performance_figure = Figure(
        build_performance_figure(results_df),
        caption=Paragraph(
            "Accuracy and latency curves generated directly from the benchmark CSV with matplotlib."
        ),
        width_inches=6.0,
    )
    ablation_figure = Figure(
        build_ablation_figure(ablation_df),
        caption=Paragraph(
            "Ablation accuracy chart generated from the ablation CSV with matplotlib."
        ),
        width_inches=5.4,
    )

    return Document(
        "A Python-Native Workflow for Reproducible Journal Manuscripts",
        Section(
            "Abstract",
            Paragraph(
                "This example models a journal submission workflow where prose, tables, and figures are assembled from ordinary Python code. Benchmark tables are loaded from CSV files with ",
                code("pandas.read_csv"),
                ", plots are created with ",
                code("matplotlib"),
                ", and DOCX, PDF, and HTML outputs are rendered from the same source document. The workflow follows the reporting discipline described in ",
                manuscript_sources.cite("reproducible-research"),
                ".",
            ),
            Paragraph(
                "The main goal is not a novel layout engine but a practical authoring pattern for research groups that already manage experimental data in scripts. By keeping analysis inputs, figure generation, and manuscript assembly in one language, the risk of stale tables and copied captions is substantially reduced.",
            ),
            Paragraph(
                italic("Keywords: "),
                "scientific reporting, document automation, reproducible workflows, Python",
            ),
            level=2,
            numbered=False,
        ),
        Section(
            "Highlights",
            BulletList(
                "Tables can be authored directly from CSV-backed DataFrames.",
                "Matplotlib figures can be inserted without saving temporary image files.",
                "The same manuscript source renders to DOCX, PDF, and HTML for review and submission.",
            ),
            level=2,
            numbered=False,
        ),
        Section(
            "Introduction",
            Paragraph(
                "Research groups often maintain result tables in spreadsheets or CSV exports while figures are assembled separately for manuscript submission. This example keeps those assets connected by treating the document itself as Python code rather than as a final formatting step applied after the analysis is complete."
            ),
            Paragraph(
                "In day-to-day practice, this matters most during late revisions. Reviewer requests frequently alter metric definitions, split boundaries, or caption wording after the manuscript draft already exists. A Python-native document pipeline reduces the amount of manual synchronization required when those changes happen close to submission."
            ),
            Paragraph(
                "The broader motivation also aligns with practical automation patterns discussed in ",
                manuscript_sources.cite("literate-programming"),
                " and with reproducible document systems such as ",
                manuscript_sources.cite("knitr"),
                ".",
            ),
            level=1,
        ),
        Section(
            "Related Work",
            Paragraph(
                "Most scientific writing systems treat the manuscript as a separate artifact that is updated after experimental analysis is complete. That split is workable for short papers, but it becomes fragile when metrics, figures, and appendix tables are regenerated several times before a deadline."
            ),
            Paragraph(
                "Notebook-heavy workflows partially close that gap, but they do not always provide a clean route to both editable DOCX output for collaborators and stable PDF output for submission. The example here focuses on that practical bridge rather than on a new markup syntax."
            ),
            level=1,
        ),
        Section(
            "Methods",
            Section(
                "Asset Layout",
                Paragraph(
                    "The example assumes an asset directory that already contains a system diagram PNG and experiment result CSV files. That layout mirrors a small research project more closely than generating every asset inline, because diagrams and benchmark exports usually already exist before the final manuscript is assembled."
                ),
                Paragraph(
                    "Static figures remain valuable even in a programmable workflow. Architecture diagrams, annotation guidelines, and interface screenshots are often authored once and reused throughout the project. They belong under version control beside the manuscript script, not inside the rendered document output directory."
                ),
                system_diagram,
                level=2,
            ),
            Section(
                "Data Integration",
                Paragraph(
                    "The benchmark and ablation tables below are loaded from CSV files into DataFrames before being passed directly into ",
                    code("Table.from_dataframe(...)"),
                    ". The performance plots are produced from the same DataFrames and inserted as live matplotlib figure objects."
                ),
                Paragraph(
                    "This pattern keeps manuscript content close to the analysis interface. If an experiment is rerun and the CSV changes, the rendered table and chart update together without requiring a manual export step or a copied spreadsheet image."
                ),
                level=2,
            ),
            Section(
                "Reporting Protocol",
                Paragraph(
                    "The reporting protocol used in this example emphasizes three operational rules: first, every table should originate from structured data rather than hand-edited text; second, every derived figure should be generated from the same data source as the reported metric; third, manuscript claims should cite either a source or a concrete table or figure."
                ),
                Paragraph(
                    "These rules are intentionally modest. They do not require a full experiment-tracking system, but they do force the manuscript to remain downstream of the evidence instead of being edited independently from it."
                ),
                level=2,
            ),
            level=1,
        ),
        Section(
            "Experimental Setup",
            Paragraph(
                "The study corpus combines structured system logs with editorial metadata and held-out blind-review documents. The split summary is shown in ",
                dataset_table,
                ". In a real project, this small table would usually be derived from the same preprocessing script that produced the training and evaluation files."
            ),
            dataset_table,
            Paragraph(
                "All benchmark runs are reported with the same evaluation harness and the same fixed review checklist. The objective here is not to maximize raw model performance but to demonstrate how a manuscript can stay synchronized with small but realistic research assets."
            ),
            level=1,
        ),
        Section(
            "Results",
            Section(
                "Benchmark Performance",
                Paragraph(
                    "As summarized in ",
                    benchmark_table,
                    ", the held-out evaluation set improves as more review automation is added. The same CSV data is visualized in ",
                    performance_figure,
                    ", which makes the accuracy-latency tradeoff easier to compare during revision meetings.",
                ),
                Paragraph(
                    "The final configuration increases accuracy by more than six points over the baseline while preserving a latency profile that remains operationally acceptable for editorial review. In many applied settings, that type of balanced gain matters more than the single best score in isolation."
                ),
                benchmark_table,
                performance_figure,
                level=2,
            ),
            Section(
                "Ablation Study",
                Paragraph(
                    "A smaller ablation CSV can be inserted without changing the document model. The same path from CSV to DataFrame to renderable table is reused for ",
                    ablation_table,
                    ", and the corresponding chart in ",
                    ablation_figure,
                    " provides a quicker view of the performance impact of each design decision.",
                ),
                Paragraph(
                    "The ablation pattern is useful when a paper evolves rapidly. As additional controls or variants are added late in the project, the authoring code changes very little because the manuscript is already prepared to consume structured experiment outputs."
                ),
                ablation_table,
                ablation_figure,
                level=2,
            ),
            level=1,
        ),
        Section(
            "Qualitative Analysis",
            Paragraph(
                "Beyond scalar metrics, the workflow also supports qualitative discussion anchored to the same evidence. During manuscript revision, teams can place reviewer commentary, illustrative figures, and supplementary tables close to the sections that interpret them, rather than distributing that information across spreadsheets, slide decks, and a separate word-processing document."
            ),
            Paragraph(
                "That consolidation is especially helpful when several authors share ownership of the same paper. The experimental asset paths remain explicit, the document structure remains readable, and the rendered output still looks like a conventional manuscript rather than a notebook export."
            ),
            level=1,
        ),
        Section(
            "Discussion",
            Paragraph(
                "For many applied teams, the primary value is not a new layout feature but the reduction in manual copying. When tables and figures are regenerated from the same inputs that produced the analysis, late revisions become safer and faster. Errors that used to survive because of stale captions or copied spreadsheet cells become easier to catch in code review."
            ),
            Paragraph(
                "There are still tradeoffs. A programmable manuscript requires discipline in project layout, and teams that are unfamiliar with Python packaging may initially find the asset and dependency setup less familiar than a pure word-processor workflow. In return, they gain stronger traceability between reported results and underlying data."
            ),
            level=1,
        ),
        Section(
            "Conclusion",
            Paragraph(
                "This example shows a practical middle ground between hand-authored manuscripts and fully bespoke publishing systems. A small amount of structured Python code is enough to keep CSV-backed tables, matplotlib figures, citations, and submission-ready outputs aligned throughout the writing process."
            ),
            level=1,
        ),
        Section(
            "Acknowledgements",
            Paragraph(
                "The authors thank the internal review group for feedback on manuscript structure, benchmark presentation, and the reproducibility checklist used during drafting."
            ),
            level=2,
            numbered=False,
        ),
        ReferencesPage(),
        author="Jiyoon Kim; Minho Lee; Sujin Park",
        summary="Journal-style example manuscript",
        authors=["Jiyoon Kim, Minho Lee, and Sujin Park"],
        affiliations=["Department of Computational Publishing, Seoul"],
        theme=Theme(page_number_format="{page}"),
        citations=manuscript_sources,
    )


def build_journal_paper(output_dir: str | Path) -> tuple[Path, Path]:
    """Build the journal paper example and export it to DOCX, PDF, and HTML."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document = build_journal_paper_document()
    docx_path = output_path / "journal-paper.docx"
    pdf_path = output_path / "journal-paper.pdf"
    html_path = output_path / "journal-paper.html"
    document.save_docx(docx_path)
    document.save_pdf(pdf_path)
    document.save_html(html_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the paper into the default example output directory."""

    docx_path, pdf_path = build_journal_paper(OUTPUT_DIR)
    html_path = OUTPUT_DIR / "journal-paper.html"
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
