"""Inline text fragments and helper constructors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence, TYPE_CHECKING

from docscriptor.equations import equation_plain_text
from docscriptor.styles import TextStyle

if TYPE_CHECKING:
    from docscriptor.references import CitationSource


@dataclass(slots=True)
class Text:
    """Base inline text fragment.

    Args:
        value: Literal text content.
        style: Optional inline style overrides.
    """

    value: str
    style: TextStyle = field(default_factory=TextStyle)

    def plain_text(self) -> str:
        """Return the fragment without styling metadata."""

        return self.value

    @classmethod
    def styled(cls, value: str, **style_values: object) -> Text:
        """Create a plain text fragment with an inline ``TextStyle``."""

        return cls(value=value, style=TextStyle(**style_values))

    @classmethod
    def bold(cls, value: str, style: TextStyle | None = None) -> Bold:
        """Create a bold text fragment."""

        return Bold(value, style=style)

    @classmethod
    def italic(cls, value: str, style: TextStyle | None = None) -> Italic:
        """Create an italic text fragment."""

        return Italic(value, style=style)

    @classmethod
    def code(cls, value: str, style: TextStyle | None = None) -> Monospace:
        """Create a monospace text fragment."""

        return Monospace(value, style=style)

    @classmethod
    def color(
        cls,
        value: str,
        color: str,
        style: TextStyle | None = None,
    ) -> Text:
        """Create a colored text fragment."""

        return cls(
            value=value,
            style=TextStyle(color=color).merged(style),
        )

    @classmethod
    def from_markup(
        cls,
        source: str,
        *,
        style: TextStyle | None = None,
    ) -> list[Text]:
        """Parse simple markdown-like markup into inline fragments."""

        from docscriptor.markup import markup

        return markup(source, style=style)


class Bold(Text):
    """Bold inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(bold=True).merged(style))


class Italic(Text):
    """Italic inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle(italic=True).merged(style))


class Monospace(Text):
    """Monospace inline text."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(
            value=value,
            style=TextStyle(font_name="Courier New").merged(style),
        )


Strong = Bold
Emphasis = Italic
Code = Monospace


class BlockReference(Text):
    """Inline reference to a numbered table or figure block."""

    __slots__ = ("target",)

    def __init__(self, target: object, style: TextStyle | None = None) -> None:
        super().__init__(value="", style=style or TextStyle())
        self.target = target

    def plain_text(self) -> str:
        """Return a placeholder reference string before numbering is resolved."""

        label = "Figure" if type(self.target).__name__ == "Figure" else "Table"
        return f"{label} ?"


class Citation(Text):
    """Inline citation rendered from a bibliography entry or key."""

    __slots__ = ("target",)

    def __init__(self, target: CitationSource | str, style: TextStyle | None = None) -> None:
        super().__init__(value="", style=style or TextStyle())
        self.target = target

    def plain_text(self) -> str:
        """Return a placeholder citation label."""

        return "[?]"

    @classmethod
    def reference(
        cls,
        target: CitationSource | str,
        *,
        style: TextStyle | None = None,
    ) -> Citation:
        """Create an inline citation fragment."""

        return cls(target, style=style)


def cite(target: CitationSource | str, *, style: TextStyle | None = None) -> Citation:
    """Compatibility helper for inline citation creation."""

    return Citation.reference(target, style=style)


class Hyperlink(Text):
    """Inline hyperlink to an external URL or internal anchor."""

    __slots__ = ("target", "label", "internal")

    def __init__(
        self,
        target: str,
        *label: InlineInput,
        internal: bool = False,
        style: TextStyle | None = None,
    ) -> None:
        super().__init__(
            value="",
            style=TextStyle(color="0563C1", underline=True).merged(style),
        )
        self.target = target
        self.label = coerce_inlines(label or (target,))
        self.internal = internal

    def plain_text(self) -> str:
        """Return the visible hyperlink label."""

        return "".join(fragment.plain_text() for fragment in self.label)

    @classmethod
    def external(
        cls,
        target: str,
        *label: InlineInput,
        style: TextStyle | None = None,
    ) -> Hyperlink:
        """Create an external hyperlink."""

        return cls(target, *label, internal=False, style=style)

    @classmethod
    def internal_anchor(
        cls,
        target: str,
        *label: InlineInput,
        style: TextStyle | None = None,
    ) -> Hyperlink:
        """Create an internal hyperlink."""

        return cls(target, *label, internal=True, style=style)


class Comment(Text):
    """Inline text annotated with a numbered comment."""

    __slots__ = ("comment", "author", "initials")

    def __init__(
        self,
        value: str,
        *comment: InlineInput,
        author: str | None = None,
        initials: str | None = None,
        style: TextStyle | None = None,
    ) -> None:
        super().__init__(value=value, style=style or TextStyle())
        self.comment = coerce_inlines(comment)
        self.author = author
        self.initials = initials

    def plain_text(self) -> str:
        """Return the visible inline text with a placeholder marker."""

        return f"{self.value}[?]"

    @classmethod
    def annotated(
        cls,
        value: str,
        *note: InlineInput,
        author: str | None = None,
        initials: str | None = None,
        style: TextStyle | None = None,
    ) -> Comment:
        """Create inline text with an attached numbered comment."""

        return cls(
            value,
            *note,
            author=author,
            initials=initials,
            style=style,
        )


def comment(
    value: str,
    *note: InlineInput,
    author: str | None = None,
    initials: str | None = None,
    style: TextStyle | None = None,
) -> Comment:
    """Compatibility helper for comment creation."""

    return Comment.annotated(
        value,
        *note,
        author=author,
        initials=initials,
        style=style,
    )


class Footnote(Text):
    """Inline text annotated with a numbered portable footnote."""

    __slots__ = ("note",)

    def __init__(
        self,
        value: str,
        *note: InlineInput,
        style: TextStyle | None = None,
    ) -> None:
        super().__init__(value=value, style=style or TextStyle())
        self.note = coerce_inlines(note)

    def plain_text(self) -> str:
        """Return the visible inline text with a placeholder marker."""

        return f"{self.value}[?]"

    @classmethod
    def annotated(
        cls,
        value: str,
        *note: InlineInput,
        style: TextStyle | None = None,
    ) -> Footnote:
        """Create inline text with an attached numbered footnote."""

        return cls(value, *note, style=style)


def footnote(
    value: str,
    *note: InlineInput,
    style: TextStyle | None = None,
) -> Footnote:
    """Compatibility helper for footnote creation."""

    return Footnote.annotated(value, *note, style=style)


class Math(Text):
    """Inline math fragment written in lightweight LaTeX syntax."""

    def __init__(self, value: str, style: TextStyle | None = None) -> None:
        super().__init__(value=value, style=TextStyle().merged(style))

    def plain_text(self) -> str:
        """Return a readable plain-text math approximation."""

        return equation_plain_text(self.value)

    @classmethod
    def inline(cls, value: str, *, style: TextStyle | None = None) -> Math:
        """Create an inline math fragment."""

        return cls(value, style=style)


def math(value: str, *, style: TextStyle | None = None) -> Math:
    """Compatibility helper for inline math creation."""

    return Math.inline(value, style=style)


def styled(value: str, **style_values: object) -> Text:
    """Compatibility helper for styled inline text."""

    return Text.styled(value, **style_values)


def bold(value: str, *, style: TextStyle | None = None) -> Bold:
    """Compatibility helper for bold inline text."""

    return Text.bold(value, style=style)


def italic(value: str, *, style: TextStyle | None = None) -> Italic:
    """Compatibility helper for italic inline text."""

    return Text.italic(value, style=style)


def code(value: str, *, style: TextStyle | None = None) -> Monospace:
    """Compatibility helper for monospace inline text."""

    return Text.code(value, style=style)


def color(
    value: str,
    color: str,
    *,
    style: TextStyle | None = None,
) -> Text:
    """Compatibility helper for colored inline text."""

    return Text.color(value, color, style=style)


def link(
    target: str,
    *label: InlineInput,
    style: TextStyle | None = None,
) -> Hyperlink:
    """Compatibility helper for hyperlink creation."""

    return Hyperlink.external(target, *label, style=style)


InlineInput = Text | str | Sequence["InlineInput"] | None


def coerce_inlines(values: Iterable[InlineInput]) -> list[Text]:
    """Normalize supported inline inputs into ``Text`` fragments."""

    normalized: list[Text] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, Text):
            normalized.append(value)
            continue
        if _is_block_reference(value):
            normalized.append(BlockReference(value))
            continue
        if isinstance(value, str):
            normalized.append(Text(value))
            continue
        if isinstance(value, Sequence):
            normalized.extend(coerce_inlines(value))
            continue
        raise TypeError(f"Unsupported inline value: {type(value)!r}")
    return normalized


def _is_block_reference(value: object) -> bool:
    block_name = type(value).__name__
    return block_name in {"Table", "Figure"}


_BlockReference = BlockReference
