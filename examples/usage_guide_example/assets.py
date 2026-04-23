"""Static assets used by the usage guide example."""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile


EXAMPLE_DIR = Path(__file__).resolve().parent
ASSET_DIR = EXAMPLE_DIR / "assets"
FIGURE_NAME = "usage-guide-figure.png"
FIGURE_PATH = ASSET_DIR / FIGURE_NAME


def copy_usage_guide_figure(output_dir: Path) -> Path:
    """Copy the bundled guide figure into the chosen output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    target_path = output_dir / FIGURE_NAME
    copyfile(FIGURE_PATH, target_path)
    return target_path
