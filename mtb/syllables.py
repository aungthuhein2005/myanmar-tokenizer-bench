"""Burmese syllable counting (rule-based, same rules as burmese-rag's segmenter).

Syllables are the natural unit for Burmese, which has no spaces between words, so
"tokens per syllable" tells you how finely a tokenizer chops the script:
~1 means roughly one token per syllable; 3+ means it's falling back to bytes/pieces.
"""

from __future__ import annotations

import re

# Break before: an unstacked consonant not followed by asat/virama; an independent
# vowel or symbol; Myanmar punctuation; the start of a digit run or a Latin run.
_BREAK = re.compile(
    r"(?<!္)[က-အ](?![်္])"
    r"|[ဣ-ဪဿ၊-၏]"
    r"|(?<![၀-၉])[၀-၉]"
    r"|(?<![A-Za-z0-9])[A-Za-z0-9]"
)
_PUNCT = set("၊။၌၍၏!?.,;:()[]{}\"'«»“”‘’-–—")


def syllables(text: str) -> list[str]:
    out: list[str] = []
    for piece in text.split():
        marked = _BREAK.sub(lambda m: "\x00" + m.group(0), piece)
        out.extend(s for s in marked.split("\x00") if s)
    return out


def count_syllables(text: str) -> int:
    """Syllables excluding punctuation."""
    return sum(1 for s in syllables(text) if s not in _PUNCT)
