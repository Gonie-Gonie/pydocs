"""Helpers for simple inline markup parsing."""

from __future__ import annotations

from docscriptor.model import Code, Emphasis, Strong, Text, TextStyle


def markup(source: str, *, style: TextStyle | None = None) -> list[Text]:
    """Parse a lightweight markdown-like inline string."""

    base_style = style or TextStyle()
    return _parse_markup(source, base_style)


def md(source: str, *, style: TextStyle | None = None) -> list[Text]:
    """Short alias for markup()."""

    return markup(source, style=style)


def _parse_markup(source: str, base_style: TextStyle) -> list[Text]:
    fragments: list[Text] = []
    cursor = 0
    length = len(source)

    while cursor < length:
        if source.startswith("**", cursor):
            end = source.find("**", cursor + 2)
            if end != -1:
                fragments.extend(_rebase(markup(source[cursor + 2 : end]), base_style.merged(TextStyle(bold=True))))
                cursor = end + 2
                continue
        if source[cursor] == "*":
            end = source.find("*", cursor + 1)
            if end != -1:
                fragments.extend(_rebase(markup(source[cursor + 1 : end]), base_style.merged(TextStyle(italic=True))))
                cursor = end + 1
                continue
        if source[cursor] == "`":
            end = source.find("`", cursor + 1)
            if end != -1:
                fragments.append(Code(source[cursor + 1 : end], style=base_style))
                cursor = end + 1
                continue

        next_positions = [
            position
            for position in (
                source.find("**", cursor),
                source.find("*", cursor),
                source.find("`", cursor),
            )
            if position != -1
        ]
        next_marker = min(next_positions, default=length)
        if next_marker == cursor:
            next_marker = cursor + 1
        fragments.append(Text(source[cursor:next_marker], style=base_style))
        cursor = next_marker

    return fragments


def _rebase(fragments: list[Text], style: TextStyle) -> list[Text]:
    rebased: list[Text] = []
    for fragment in fragments:
        if isinstance(fragment, Strong):
            rebased.append(Strong(fragment.value, style=style.merged(fragment.style)))
        elif isinstance(fragment, Emphasis):
            rebased.append(Emphasis(fragment.value, style=style.merged(fragment.style)))
        elif isinstance(fragment, Code):
            rebased.append(Code(fragment.value, style=style.merged(fragment.style)))
        else:
            rebased.append(Text(fragment.value, style=style.merged(fragment.style)))
    return rebased
