"""Helpers for lightweight LaTeX-style equation rendering."""

from __future__ import annotations

from dataclasses import dataclass


BASELINE = "baseline"
SUPERSCRIPT = "superscript"
SUBSCRIPT = "subscript"

VERTICAL_ALIGNMENTS = {BASELINE, SUPERSCRIPT, SUBSCRIPT}


LATEX_SYMBOLS = {
    ",": " ",
    ";": "  ",
    "!": "",
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ϵ",
    "varepsilon": "ε",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "vartheta": "ϑ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "varpi": "ϖ",
    "rho": "ρ",
    "varrho": "ϱ",
    "sigma": "σ",
    "varsigma": "ς",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "varphi": "ϕ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Xi": "Ξ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Upsilon": "Υ",
    "Phi": "Φ",
    "Psi": "Ψ",
    "Omega": "Ω",
    "cdot": "·",
    "times": "×",
    "pm": "±",
    "mp": "∓",
    "neq": "≠",
    "ne": "≠",
    "leq": "≤",
    "geq": "≥",
    "approx": "≈",
    "sim": "∼",
    "equiv": "≡",
    "propto": "∝",
    "infty": "∞",
    "partial": "∂",
    "nabla": "∇",
    "sum": "∑",
    "prod": "∏",
    "int": "∫",
    "oint": "∮",
    "forall": "∀",
    "exists": "∃",
    "in": "∈",
    "notin": "∉",
    "subset": "⊂",
    "subseteq": "⊆",
    "supset": "⊃",
    "supseteq": "⊇",
    "cup": "∪",
    "cap": "∩",
    "vee": "∨",
    "wedge": "∧",
    "to": "→",
    "rightarrow": "→",
    "leftarrow": "←",
    "leftrightarrow": "↔",
    "Rightarrow": "⇒",
    "Leftarrow": "⇐",
    "Leftrightarrow": "⇔",
    "ldots": "…",
    "cdots": "⋯",
    "dots": "…",
    "mid": "|",
    "vert": "|",
    "Vert": "‖",
    "degree": "°",
}

GROUP_COMMANDS = {"text", "mathrm", "mathit", "mathbf", "operatorname", "operatorname*"}

DELIMITER_COMMANDS = {"left", "right"}


@dataclass(slots=True)
class EquationSegment:
    """Text fragment plus a vertical alignment hint."""

    text: str
    vertical_align: str = BASELINE

    def __post_init__(self) -> None:
        if self.vertical_align not in VERTICAL_ALIGNMENTS:
            raise ValueError(f"Unsupported vertical alignment: {self.vertical_align!r}")


def parse_latex_segments(source: str) -> list[EquationSegment]:
    """Parse a lightweight LaTeX-like expression into styled text segments."""

    parser = _EquationParser(source)
    return _merge_adjacent(parser.parse())


def equation_plain_text(source: str) -> str:
    """Return a readable plain-text form of a LaTeX-like expression."""

    return "".join(segment.text for segment in parse_latex_segments(source))


class _EquationParser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0

    def parse(self, stop_char: str | None = None) -> list[EquationSegment]:
        segments: list[EquationSegment] = []
        while self.position < len(self.source):
            char = self.source[self.position]
            if stop_char is not None and char == stop_char:
                self.position += 1
                break
            if char == "{":
                self.position += 1
                segments.extend(self.parse(stop_char="}"))
                continue
            if char == "}":
                self.position += 1
                continue
            if char == "\\":
                segments.extend(self._parse_command())
                continue
            if char in "^_":
                self.position += 1
                aligned = SUPERSCRIPT if char == "^" else SUBSCRIPT
                token = self._read_token()
                segments.extend(_apply_vertical_alignment(token, aligned))
                continue
            segments.append(EquationSegment(char))
            self.position += 1
        return segments

    def _parse_command(self) -> list[EquationSegment]:
        self.position += 1
        if self.position >= len(self.source):
            return [EquationSegment("\\")]

        start = self.position
        if self.source[self.position].isalpha():
            while self.position < len(self.source) and self.source[self.position].isalpha():
                self.position += 1
            command = self.source[start:self.position]
        else:
            command = self.source[self.position]
            self.position += 1

        if command in DELIMITER_COMMANDS:
            return self._parse_delimiter()
        if command in GROUP_COMMANDS:
            return self._read_token()
        if command in {"frac", "dfrac", "tfrac"}:
            numerator = self._read_token()
            denominator = self._read_token()
            return [EquationSegment("(")] + numerator + [EquationSegment(")/(")] + denominator + [EquationSegment(")")]
        if command == "sqrt":
            radicand = self._read_token()
            return [EquationSegment("√(")] + radicand + [EquationSegment(")")]
        if command == "overline":
            return self._read_token()
        if command in {"quad", "qquad"}:
            return [EquationSegment("  " if command == "quad" else "    ")]
        if command == "\\":
            return [EquationSegment("\n")]
        if command in LATEX_SYMBOLS:
            return [EquationSegment(LATEX_SYMBOLS[command])]
        return [EquationSegment(f"\\{command}")]

    def _parse_delimiter(self) -> list[EquationSegment]:
        if self.position >= len(self.source):
            return []
        delimiter = self.source[self.position]
        self.position += 1
        if delimiter == ".":
            return []
        if delimiter == "\\":
            return self._parse_command()
        return [EquationSegment(delimiter)]

    def _read_token(self) -> list[EquationSegment]:
        if self.position >= len(self.source):
            return []
        if self.source[self.position] == "{":
            self.position += 1
            return self.parse(stop_char="}")
        if self.source[self.position] == "\\":
            return self._parse_command()
        token = [EquationSegment(self.source[self.position])]
        self.position += 1
        return token


def _apply_vertical_alignment(segments: list[EquationSegment], vertical_align: str) -> list[EquationSegment]:
    aligned: list[EquationSegment] = []
    for segment in segments:
        if not segment.text:
            continue
        aligned.append(EquationSegment(segment.text, vertical_align=vertical_align))
    return aligned


def _merge_adjacent(segments: list[EquationSegment]) -> list[EquationSegment]:
    merged: list[EquationSegment] = []
    for segment in segments:
        if not segment.text:
            continue
        if merged and merged[-1].vertical_align == segment.vertical_align:
            merged[-1] = EquationSegment(merged[-1].text + segment.text, vertical_align=segment.vertical_align)
        else:
            merged.append(segment)
    return merged
