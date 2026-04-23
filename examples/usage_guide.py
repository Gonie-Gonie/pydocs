"""Compatibility wrapper for the package-style usage guide example."""

from examples.usage_guide_example import (
    build_usage_guide,
    build_usage_guide_document,
    main,
)

__all__ = ["build_usage_guide", "build_usage_guide_document", "main"]


if __name__ == "__main__":
    main()
