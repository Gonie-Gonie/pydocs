"""Citation data used by the usage guide example."""

from __future__ import annotations

from docscriptor import CitationSource
from docscriptor.references import CitationLibrary


RELATED_WORK_BIBTEX = """@article{knuth1984literate,
  author = {Donald E. Knuth},
  title = {Literate Programming},
  journal = {The Computer Journal},
  volume = {27},
  number = {2},
  pages = {97--111},
  year = {1984},
  publisher = {Oxford University Press},
  url = {https://doi.org/10.1093/comjnl/27.2.97}
}"""


def build_repository_source() -> CitationSource:
    """Return the repository citation used in the guide narrative."""

    return CitationSource(
        "pydocs",
        organization="Gonie-Gonie",
        publisher="GitHub repository",
        year="2026",
        url="https://github.com/Gonie-Gonie/pydocs",
    )


def build_related_work_library() -> CitationLibrary:
    """Return the small related-work bibliography used by the guide."""

    return CitationLibrary.from_bibtex(RELATED_WORK_BIBTEX)
