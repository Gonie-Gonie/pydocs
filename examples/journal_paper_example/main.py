"""Standalone journal paper example for docscriptor."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from docscriptor import (
    Affiliation,
    Author,
    BulletList,
    CitationLibrary,
    CitationSource,
    Document,
    DocumentSettings,
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


OUTPUT_DIR = Path("artifacts") / "journal-paper"
EXAMPLE_DIR = Path(__file__).resolve().parent
ASSET_DIR = EXAMPLE_DIR / "assets"
RESULTS_CSV_PATH = ASSET_DIR / "benchmark_results.csv"
ABLATION_CSV_PATH = ASSET_DIR / "ablation_results.csv"


def _wrapped_lines(lines: list[str], *, width: int) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(fill(line, width=width).splitlines())
    return wrapped


def _add_box(
    axis: object,
    x: float,
    y: float,
    width: float,
    height: float,
    color_value: str,
    title: str,
    lines: list[str],
    *,
    wrap_width: int = 21,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.2,
        edgecolor="#455E74",
        facecolor=color_value,
    )
    axis.add_patch(patch)
    axis.text(
        x + width / 2,
        y + height - 0.07,
        title,
        ha="center",
        va="top",
        fontsize=10.5,
        weight="bold",
        color="#183244",
        clip_on=True,
    )
    wrapped = _wrapped_lines(lines, width=wrap_width)
    top = y + height - 0.16
    bottom = y + 0.07
    step = min(0.065, max((top - bottom) / max(len(wrapped), 1), 0.04))
    for index, line in enumerate(wrapped):
        axis.text(
            x + 0.03,
            top - (index * step),
            line,
            ha="left",
            va="top",
            fontsize=8.6,
            color="#23394A",
            clip_on=True,
        )


def build_traceability_figure():
    """Create a diagram showing the manuscript workflow being studied."""

    figure, axis = plt.subplots(figsize=(8.0, 3.8))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    _add_box(
        axis,
        0.05,
        0.22,
        0.205,
        0.6,
        "#EAF3FB",
        "Evidence Sources",
        [
            "Benchmark CSV files",
            "Static diagrams and logos",
            "Citation metadata",
        ],
    )
    _add_box(
        axis,
        0.31,
        0.16,
        0.225,
        0.72,
        "#F8F2E8",
        "Python Authoring Layer",
        [
            "Table.from_dataframe(...)",
            "Figure(matplotlib_object)",
            "Structured sections and notes",
        ],
        wrap_width=22,
    )
    _add_box(
        axis,
        0.59,
        0.22,
        0.17,
        0.6,
        "#EDF7EC",
        "Traceability Checks",
        [
            "Caption numbering",
            "Cross-reference targets",
            "Generated bibliography",
        ],
    )
    _add_box(
        axis,
        0.80,
        0.22,
        0.15,
        0.6,
        "#FCEDE7",
        "Submission Outputs",
        [
            "DOCX review copy",
            "PDF submission",
            "HTML sharing draft",
        ],
        wrap_width=18,
    )

    arrow_kwargs = {"arrowstyle": "->", "lw": 2.0, "color": "#48627A"}
    axis.annotate("", xy=(0.31, 0.5), xytext=(0.25, 0.5), arrowprops=arrow_kwargs)
    axis.annotate("", xy=(0.59, 0.5), xytext=(0.53, 0.5), arrowprops=arrow_kwargs)
    axis.annotate("", xy=(0.80, 0.5), xytext=(0.75, 0.5), arrowprops=arrow_kwargs)
    axis.text(0.5, 0.93, "The workflow keeps manuscript claims downstream of the evidence that supports them.", ha="center", fontsize=11, color="#183244")
    figure.tight_layout()
    return figure


def build_quality_latency_figure(results_df: pd.DataFrame):
    """Plot the quality-latency frontier from the benchmark CSV."""

    figure, axis = plt.subplots(figsize=(6.4, 3.4))
    palette = ["#6C8DB0", "#4F8DA1", "#3F9D79", "#D07B42"]
    axis.scatter(results_df["Latency_ms"], results_df["Accuracy"], s=180, c=palette, edgecolors="#173042", linewidths=1.0)
    axis.plot(results_df["Latency_ms"], results_df["Accuracy"], color="#7B8E9E", linestyle="--", linewidth=1.5)
    for _, row in results_df.iterrows():
        axis.annotate(
            row["Model"],
            (row["Latency_ms"], row["Accuracy"]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8.5,
            color="#173042",
        )
    axis.set_xlabel("Latency (ms)")
    axis.set_ylabel("Accuracy")
    axis.set_ylim(0.865, 0.95)
    axis.set_title("Quality-Latency Frontier")
    axis.grid(alpha=0.25, linestyle=":")
    figure.tight_layout()
    return figure


def build_revision_effort_figure():
    """Plot the expected synchronization effort during late revisions."""

    revision_rounds = [1, 2, 3, 4]
    manual_minutes = [36, 49, 63, 79]
    docscriptor_minutes = [18, 21, 25, 29]

    figure, axis = plt.subplots(figsize=(6.4, 3.4))
    axis.plot(revision_rounds, manual_minutes, marker="o", linewidth=2.5, color="#D06A44", label="Manual document synchronization")
    axis.plot(revision_rounds, docscriptor_minutes, marker="o", linewidth=2.5, color="#3F8F6B", label="Docscriptor-based synchronization")
    axis.fill_between(revision_rounds, docscriptor_minutes, manual_minutes, color="#F6D8CB", alpha=0.45)
    axis.set_xlabel("Late revision round")
    axis.set_ylabel("Estimated minutes per update")
    axis.set_xticks(revision_rounds)
    axis.set_title("Operational Cost of Late Revisions")
    axis.legend(frameon=False, fontsize=8.5)
    axis.grid(alpha=0.25, linestyle=":")
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
            ["Test", 2600, "blind review split"],
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

    dataset_table = Table.from_dataframe(
        dataset_df,
        caption="Study corpus used to evaluate the manuscript workflow.",
        column_widths=[1.2, 1.2, 3.2],
        style=TableStyle(
            header_background_color="#E7EEF7",
            alternate_row_background_color="#FAFCFE",
        ),
    )
    benchmark_table = Table.from_dataframe(
        results_df[["Model", "Accuracy", "F1", "Latency_ms"]],
        caption="Benchmark results loaded directly from the experiment CSV file.",
        column_widths=[2.0, 1.0, 0.9, 1.3],
        style=TableStyle(
            header_background_color="#DCE8F4",
            alternate_row_background_color="#F7FAFD",
        ),
    )
    ablation_table = Table.from_dataframe(
        ablation_df,
        caption="Ablation results for the manuscript automation workflow.",
        column_widths=[2.9, 1.0, 1.2],
        style=TableStyle(
            header_background_color="#E3ECF6",
            alternate_row_background_color="#F8FBFD",
        ),
    )

    traceability_figure = Figure(
        build_traceability_figure(),
        caption=Paragraph(
            "Traceability pipeline used in the study, linking evidence sources, authored structure, checks, and submission outputs."
        ),
        width=6.2,
    )
    quality_latency_figure = Figure(
        build_quality_latency_figure(results_df),
        caption=Paragraph(
            "Quality-latency frontier derived directly from the benchmark CSV used in the manuscript."
        ),
        width=6.0,
    )
    revision_effort_figure = Figure(
        build_revision_effort_figure(),
        caption=Paragraph(
            "Estimated late-revision synchronization effort comparing manual workflows with a docscriptor-based workflow."
        ),
        width=6.0,
    )

    return Document(
        "Docscriptor Development Philosophy",
        Section(
            "Abstract",
            Paragraph(
                "This example models a journal submission workflow in which prose, tables, figures, and citations are assembled from ordinary Python code. Benchmark tables are loaded from CSV files with ",
                code("pandas.read_csv"),
                ", explanatory figures are generated with ",
                code("matplotlib"),
                ", and DOCX, PDF, and HTML outputs are rendered from the same source document. The workflow follows the reproducibility discipline discussed in ",
                manuscript_sources.cite("reproducible-research"),
                ".",
            ),
            Paragraph(
                "The paper argues for a practical authoring pattern rather than a new publishing format. The central claim is that keeping manuscript structure downstream of the evidence reduces synchronization mistakes during late revisions and makes document review easier to trust."
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
                "Journal-style title matter can be authored from structured metadata without giving up customization paths.",
                "Tables and figures can be regenerated from the same Python inputs that support the manuscript claims.",
                "The strongest workflow benefit appears during late revisions, when synchronization cost usually rises fastest.",
            ),
            level=2,
            numbered=False,
        ),
        Section(
            "Introduction",
            Paragraph(
                "Research manuscripts often combine at least four moving parts: benchmark tables, static diagrams, generated plots, and conventional prose. In many teams those assets are edited in different tools, which creates avoidable synchronization work every time a metric, caption, or section ordering changes."
            ),
            Paragraph(
                "The workflow studied here treats the manuscript itself as code. That does not eliminate editorial work, but it does move the document closer to the data that supports it, which is the operational direction already suggested by ",
                manuscript_sources.cite("literate-programming"),
                " and systems such as ",
                manuscript_sources.cite("knitr"),
                ".",
            ),
            level=1,
        ),
        Section(
            "Workflow Design",
            Section(
                "Evidence Traceability",
                Paragraph(
                    "The study begins from a straightforward design requirement: every visible claim should remain traceable to either structured input data, a generated figure, or a cited source. ",
                    traceability_figure,
                    " summarizes the resulting workflow."
                ),
                Paragraph(
                    "The intent is not to force authors into a notebook-like page. Instead, the workflow preserves manuscript conventions such as abstract sections, captions, and editable review copies while keeping those conventions downstream of the evidence."
                ),
                traceability_figure,
                level=2,
            ),
            Section(
                "Operational Rules",
                Paragraph(
                    "Three rules were enforced in the example manuscript. First, numeric tables must originate from structured data rather than hand-edited cells. Second, generated figures must be built from the same inputs that support the reported metric. Third, manuscript claims should cite a source or point to a table or figure wherever the argument depends on evidence."
                ),
                Paragraph(
                    "These rules are deliberately modest. They can be adopted in a small project without introducing a full experiment-tracking platform, yet they materially reduce the number of unreviewable document edits."
                ),
                level=2,
            ),
            level=1,
        ),
        Section(
            "Study Assets",
            Paragraph(
                "The evaluation uses a small but realistic asset bundle: benchmark result CSV files, an ablation CSV, structured citation metadata, and an authored manuscript script. The corpus summary is shown in ",
                dataset_table,
                "."
            ),
            dataset_table,
            Paragraph(
                "The important point is not the corpus size by itself. The point is that the visible document objects and the supporting data remain connected through explicit code rather than through manual export steps."
            ),
            level=1,
        ),
        Section(
            "Results",
            Section(
                "Benchmark Frontier",
                Paragraph(
                    "The benchmark data in ",
                    benchmark_table,
                    " shows a steady quality gain as more structure is added to the workflow. The same CSV is also rendered into ",
                    quality_latency_figure,
                    ", which makes the trade-off between quality and latency easier to interpret during revision discussions."
                ),
                Paragraph(
                    "The relevant result is not merely the best final score. The more useful observation is that the quality improvement remains interpretable because the comparison table and the comparison plot are generated from the same underlying CSV."
                ),
                benchmark_table,
                quality_latency_figure,
                level=2,
            ),
            Section(
                "Ablation Signals",
                Paragraph(
                    "Ablation results are summarized in ",
                    ablation_table,
                    ". Removing table automation, citation checks, or asset reuse each weakens the final result, which supports the claim that the workflow benefit comes from coordinated authoring behavior rather than from any single isolated feature."
                ),
                Paragraph(
                    "The value of the ablation is conceptual as much as numeric: it demonstrates that manuscript reliability depends on several small pieces staying connected, including caption generation, citation handling, and predictable asset reuse."
                ),
                ablation_table,
                level=2,
            ),
            Section(
                "Late-Revision Cost",
                Paragraph(
                    "The workflow benefit becomes most visible late in the writing cycle. ",
                    revision_effort_figure,
                    " reports an estimated operational curve for repeated late updates. The estimate is intentionally approximate, but it captures a practical pattern: manual synchronization cost tends to rise more quickly than code-backed synchronization cost when the manuscript is revised several times close to submission."
                ),
                Paragraph(
                    "This type of figure matters because many workflow decisions are justified by revision logistics rather than by accuracy alone. Even when two pipelines can represent the same final content, the cheaper revision path is usually the one that survives into regular team use."
                ),
                revision_effort_figure,
                level=2,
            ),
            level=1,
        ),
        Section(
            "Discussion",
            Paragraph(
                "The example does not claim that every writing task should become a programming task. The stronger claim is narrower: when a project already depends on Python for data handling and figure generation, keeping the manuscript in the same environment improves traceability and usually reduces late-stage synchronization mistakes."
            ),
            Paragraph(
                "There are still tradeoffs. A programmable manuscript requires some repository discipline, and teams unfamiliar with packaging or automated builds may need a small onboarding step. In return, they gain a workflow where visible manuscript changes can be reviewed with the same habits used for code changes."
            ),
            level=1,
        ),
        Section(
            "Conclusion",
            Paragraph(
                "This journal example shows docscriptor at its most manuscript-oriented: structured authorship, data-backed tables, explanatory figures, and submission-ready exports are kept in one readable Python source. The result is not just reproducible output, but a document workflow that is easier to revise and easier to trust."
            ),
            level=1,
        ),
        Section(
            "Acknowledgements",
            Paragraph(
                "The authors thank the internal review group for feedback on figure clarity, manuscript structure, and release packaging decisions."
            ),
            level=2,
            numbered=False,
        ),
        ReferencesPage(),
        settings=DocumentSettings(
            summary="Journal-style development philosophy paper",
            authors=[
                Author(
                    "Hyeong-Gon Jo",
                    affiliations=[
                        Affiliation(
                            department="Building Simulation LAB",
                            organization="Seoul National University",
                            city="Seoul",
                            country="Republic of Korea",
                        )
                    ],
                    corresponding=True,
                    email="gonie@example.org",
                    orcid="0009-0004-8821-275X",
                    note="GitHub: @Gonie-Gonie",
                ),
                Author(
                    "Codex",
                    affiliations=[Affiliation(organization="OpenAI")],
                    position="Coding Agent",
                    note="GitHub: openai/codex",
                ),
            ],
            theme=Theme(show_page_numbers=True, page_number_format="{page}"),
        ),
        citations=manuscript_sources,
    )


def build_journal_paper(output_dir: str | Path) -> tuple[Path, Path]:
    """Build the journal paper example and export it to DOCX, PDF, and HTML."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document = build_journal_paper_document()
    docx_path = output_path / "docscriptor-development-philosophy.docx"
    pdf_path = output_path / "docscriptor-development-philosophy.pdf"
    html_path = output_path / "docscriptor-development-philosophy.html"
    document.save_docx(docx_path)
    document.save_pdf(pdf_path)
    document.save_html(html_path)
    return docx_path, pdf_path


def main() -> None:
    """Build the paper into the default example output directory."""

    docx_path, pdf_path = build_journal_paper(OUTPUT_DIR)
    html_path = OUTPUT_DIR / "docscriptor-development-philosophy.html"
    print(f"Wrote {docx_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
