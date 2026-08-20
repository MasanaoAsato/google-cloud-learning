#!/usr/bin/env python3

"""Line breaking and width estimation for Japanese diagram labels.

Draw.io hands HTML labels to a browser, and the browser is free to wrap CJK text
between any two characters. That is how a label like「ターゲット HTTPS プロキシ」
ends up broken between「キ」and「シ」— technically legal, visually wrong, and
invisible until someone looks at the exported image.

So this module takes the wrapping decision away from the browser. It splits a
label into units that must stay together, assembles lines that fit the available
width, and ``build_drawio.py`` emits each line as its own ``white-space: nowrap``
block. The browser then renders exactly the lines computed here, which also means
a preview rendered from the same numbers matches what Draw.io shows.

Widths are estimates, not real font metrics. They are deliberately slightly
generous so that a label the estimator calls "fits" is not borderline in the
browser. ``fits`` / ``measure`` are exposed so validators can fail loudly when a
card is too small instead of letting text silently overflow.
"""

from __future__ import annotations

import re
import unicodedata

# Width per character as a fraction of the font size, by character class.
# Calibrated against Noto Sans JP / Arial rendering in Draw.io.
FULLWIDTH = 1.0
LATIN_UPPER = 0.68
LATIN_LOWER = 0.53
DIGIT = 0.56
NARROW_PUNCT = 0.30
WIDE_PUNCT = 0.55
SPACE = 0.28
BOLD_FACTOR = 1.04

# Characters that must not start a line (行頭禁則).
NO_LINE_START = "。、．，」』）〕］｝〉》’”ぁぃぅぇぉっゃゅょゎヵヶァィゥェォッャュョヮーゝゞ々!?！？:;・"
# Characters that must not end a line (行末禁則).
NO_LINE_END = "「『（〔［｛〈《‘“"

_LATIN = re.compile(r"[0-9A-Za-z]")
_KATAKANA = re.compile(r"[ァ-ヺーヽヾｦ-ﾝ]")


def _char_class(char: str) -> str:
    """Classify a character for both width and break-opportunity decisions."""
    if char == " " or char == "　":
        return "space"
    if _LATIN.match(char):
        return "latin"
    if _KATAKANA.match(char):
        return "katakana"
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    if unicodedata.east_asian_width(char) in {"W", "F"}:
        return "wide"
    return "narrow"


def char_width(char: str, font_size: float, bold: bool = False) -> float:
    """Estimated advance width of one character in pixels."""
    cls = _char_class(char)
    if cls == "space":
        ratio = SPACE if char == " " else FULLWIDTH
    elif cls == "latin":
        if char.isdigit():
            ratio = DIGIT
        elif char.isupper():
            ratio = LATIN_UPPER
        else:
            ratio = LATIN_LOWER
    elif cls in {"katakana", "hiragana", "kanji", "wide"}:
        ratio = FULLWIDTH
    elif char in ".,:;'`|!ilI":
        ratio = NARROW_PUNCT
    else:
        ratio = WIDE_PUNCT
    return ratio * font_size * (BOLD_FACTOR if bold else 1.0)


def measure(text: str, font_size: float, bold: bool = False) -> float:
    """Estimated width of a single line in pixels."""
    return sum(char_width(char, font_size, bold) for char in text)


def tokenize(text: str) -> list[str]:
    """Split text into units that should never be broken internally.

    A run of Latin letters and digits is a word. A run of katakana is a word too —
    Japanese readers parse katakana as a single foreign term, which is why breaking
    「プロキシ」in the middle reads as a typo. Kanji and hiragana are merged into one
    unit because okurigana binds them:「束ねる」is one word, so「束 / ねる」is just as
    wrong as「プロキ / シ」. Breaks are therefore only offered where a reader already
    perceives a boundary — spaces, script changes, and punctuation.
    """
    tokens: list[str] = []
    current = ""
    current_class = ""

    def flush() -> None:
        nonlocal current, current_class
        if current:
            tokens.append(current)
        current = ""
        current_class = ""

    for char in text:
        cls = _char_class(char)
        if cls in {"kanji", "hiragana"}:
            cls = "japanese"
        # Latin words absorb internal punctuation so identifiers and paths stay whole.
        if current_class == "latin" and char in "._-/:@+":
            current += char
            continue
        if cls == current_class and cls in {"latin", "katakana", "japanese"}:
            current += char
            continue
        flush()
        current = char
        current_class = cls
    flush()
    return tokens


def _inner_break_scores(token: str) -> list[float]:
    """Score each internal position of a Japanese run as a break opportunity.

    Used only when a single run is too wide to fit any line, so something has to
    give. A kanji that follows hiragana usually starts a new word, and a particle
    usually ends one, so those positions read far better than an arbitrary cut.
    """
    scores = []
    particles = "のをにはがともでへやかもらねるすたい"
    for index in range(1, len(token)):
        before, after = token[index - 1], token[index]
        score = 0.0
        if _char_class(before) == "hiragana" and _char_class(after) == "kanji":
            score = 3.0
        elif before in particles and _char_class(after) == "kanji":
            score = 2.5
        elif _char_class(before) == "kanji" and _char_class(after) == "kanji":
            score = 1.0
        scores.append(score)
    return scores


def _split_oversized(token: str, limit: float, font_size: float, bold: bool) -> list[str]:
    """Break a token that cannot fit on its own line, preferring word boundaries."""
    scores = _inner_break_scores(token)
    pieces: list[str] = []
    start = 0
    while start < len(token):
        end = start
        best = None
        while end < len(token):
            end += 1
            if measure(token[start:end], font_size, bold) > limit and end - start > 1:
                end -= 1
                break
            position = end - 1
            if 0 < position < len(token) and scores and position - 1 < len(scores):
                if scores[position - 1] > 0 and (best is None or scores[position - 1] >= best[1]):
                    best = (end, scores[position - 1])
        if best is not None and best[0] < len(token):
            end = best[0]
        pieces.append(token[start:end])
        start = end
    return pieces


def _apply_kinsoku(lines: list[str]) -> list[str]:
    """Move characters across line boundaries so 禁則処理 holds."""
    result = [line for line in lines]
    for index in range(len(result) - 1):
        # A line must not start with punctuation such as 」or ）.
        while len(result[index + 1]) > 1 and result[index + 1][0] in NO_LINE_START:
            result[index] += result[index + 1][0]
            result[index + 1] = result[index + 1][1:]
        # A line must not end with an opening bracket.
        while len(result[index]) > 1 and result[index][-1] in NO_LINE_END:
            result[index + 1] = result[index][-1] + result[index + 1]
            result[index] = result[index][:-1]
    return [line for line in result if line]


def _atoms(paragraph: str, limit: float, font_size: float, bold: bool) -> list[str]:
    """Tokenize, then pre-split anything that cannot fit a line on its own."""
    atoms: list[str] = []
    for token in tokenize(paragraph):
        if token in {" ", "　"}:
            if atoms:
                atoms.append(" ")
            continue
        if measure(token, font_size, bold) <= limit:
            atoms.append(token)
        else:
            atoms.extend(_split_oversized(token, limit, font_size, bold))
    while atoms and atoms[-1] == " ":
        atoms.pop()
    return atoms


def _balanced_lines(
    atoms: list[str], limit: float, font_size: float, bold: bool
) -> list[str]:
    """Choose breaks that use the fewest lines and then even out the line widths.

    Greedy filling packs early lines full and leaves a stub behind — the widow in
    「転送ルール・グローバル / IP」. Optimising line count first keeps the label
    compact, and minimising squared slack second spreads the text so no line looks
    abandoned.
    """
    count = len(atoms)
    # best[i] = (lines, cost) for laying out atoms[i:]
    best: list[tuple[float, float]] = [(0.0, 0.0)] * (count + 1)
    choice = [count] * (count + 1)
    for start in range(count - 1, -1, -1):
        best[start] = (float("inf"), float("inf"))
        for end in range(start + 1, count + 1):
            text = "".join(atoms[start:end]).strip()
            if not text:
                continue
            width = measure(text, font_size, bold)
            if width > limit and end > start + 1:
                break
            slack = max(0.0, limit - width)
            tail_lines, tail_cost = best[end]
            candidate = (tail_lines + 1, tail_cost + slack * slack)
            if candidate < best[start]:
                best[start] = candidate
                choice[start] = end
        if best[start][0] == float("inf"):
            best[start] = (1.0, 0.0)
            choice[start] = count
    lines: list[str] = []
    index = 0
    while index < count:
        end = choice[index]
        lines.append("".join(atoms[index:end]).strip())
        index = end
    return [line for line in lines if line]


def wrap(text: str, limit: float, font_size: float, bold: bool = False) -> list[str]:
    """Break ``text`` into lines that each fit ``limit`` pixels.

    Explicit newlines in the input are honoured as hard breaks.
    """
    if limit <= 0:
        return [text]
    lines: list[str] = []
    for paragraph in text.split("\n"):
        atoms = _atoms(paragraph, limit, font_size, bold)
        if not atoms:
            continue
        lines.extend(_balanced_lines(atoms, limit, font_size, bold))
    return _apply_kinsoku(lines) or [text]


def line_height(font_size: float) -> float:
    """Line box height Draw.io uses for HTML labels."""
    return round(font_size * 1.35, 2)


def fits(
    lines: list[str],
    width: float,
    height: float,
    font_size: float,
    bold: bool = False,
) -> tuple[bool, str]:
    """Report whether wrapped lines fit a box, with a reason when they do not."""
    for line in lines:
        used = measure(line, font_size, bold)
        if used > width + 0.5:
            return False, f"line {line!r} needs {used:.0f}px but only {width:.0f}px is available"
    needed = len(lines) * line_height(font_size)
    if needed > height + 0.5:
        return False, f"{len(lines)} line(s) need {needed:.0f}px but only {height:.0f}px is available"
    return True, ""


def html_lines(lines: list[str], escape) -> str:
    """Render lines as Draw.io HTML that the browser will not re-wrap."""
    return "".join(
        f'<div style="white-space:nowrap">{escape(line)}</div>' for line in lines
    )


if __name__ == "__main__":
    import sys

    text = sys.argv[1] if len(sys.argv) > 1 else "ターゲット HTTPS プロキシ"
    limit = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
    size = float(sys.argv[3]) if len(sys.argv) > 3 else 13.0
    for line in wrap(text, limit, size):
        print(f"{measure(line, size):6.1f}px  {line}")
