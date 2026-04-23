"""Core shared utilities used across the document model and renderers."""

from __future__ import annotations

from pathlib import Path


PathLike = str | Path

COUNTER_FORMATS = {
    "decimal",
    "lower-alpha",
    "upper-alpha",
    "lower-roman",
    "upper-roman",
    "bullet",
    "none",
}


class DocscriptorError(Exception):
    """Raised when the document model cannot be rendered safely."""


def normalize_color(value: str | None) -> str | None:
    """Normalize a hex color string to six uppercase digits.

    Args:
        value: A color in ``RRGGBB`` or ``#RRGGBB`` form.

    Returns:
        The normalized uppercase ``RRGGBB`` string, or ``None`` when
        ``value`` is ``None``.

    Raises:
        ValueError: If the supplied value is not a six-digit hex color.
    """

    if value is None:
        return None

    normalized = value.strip().lstrip("#").upper()
    if len(normalized) != 6 or any(char not in "0123456789ABCDEF" for char in normalized):
        raise ValueError(f"Expected a 6-digit hex color, got: {value!r}")
    return normalized


def normalize_counter_format(value: str) -> str:
    """Validate and normalize a supported counter format name."""

    normalized = value.strip().lower()
    if normalized not in COUNTER_FORMATS:
        raise ValueError(f"Unsupported counter format: {value!r}")
    return normalized


def _alpha_counter(value: int) -> str:
    if value < 1:
        raise ValueError("Alphabetic counters require values >= 1")

    characters: list[str] = []
    number = value
    while number > 0:
        number -= 1
        characters.append(chr(ord("a") + (number % 26)))
        number //= 26
    return "".join(reversed(characters))


def _roman_counter(value: int) -> str:
    if value < 1:
        raise ValueError("Roman numeral counters require values >= 1")

    numerals = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    remaining = value
    parts: list[str] = []
    for numeral_value, glyph in numerals:
        while remaining >= numeral_value:
            parts.append(glyph)
            remaining -= numeral_value
    return "".join(parts)


def format_counter_value(value: int, counter_format: str, *, bullet: str = "\u2022") -> str:
    """Format an integer using one of the supported numbering styles.

    Args:
        value: The counter value to format.
        counter_format: One of the supported values in ``COUNTER_FORMATS``.
        bullet: The glyph to use for ``"bullet"`` format.

    Returns:
        A display-ready string for the counter.
    """

    normalized = normalize_counter_format(counter_format)
    if normalized == "decimal":
        return str(value)
    if normalized == "lower-alpha":
        return _alpha_counter(value)
    if normalized == "upper-alpha":
        return _alpha_counter(value).upper()
    if normalized == "lower-roman":
        return _roman_counter(value).lower()
    if normalized == "upper-roman":
        return _roman_counter(value)
    if normalized == "bullet":
        return bullet
    return ""
