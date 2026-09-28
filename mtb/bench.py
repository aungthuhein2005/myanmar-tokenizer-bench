"""Count tokens for every (tokenizer, language) pair and derive comparable metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .data import BASELINE, TARGET
from .registry import Tokenizer
from .syllables import count_syllables

CONTEXT = 128_000  # a common context-window size, for the "how much fits" metric


@dataclass
class Row:
    tokenizer: str
    tokenizer_name: str
    used_by: str
    lang: str
    lang_name: str
    sentences: int
    chars: int
    utf8_bytes: int
    tokens: int
    syllables: int | None = None
    # derived
    tax: float | None = None             # tokens / English tokens, same tokenizer
    chars_per_token: float | None = None
    tokens_per_syllable: float | None = None
    sentences_in_context: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def measure(tok: Tokenizer, corpus: dict[str, list[str]], names: dict[str, str]) -> list[Row]:
    """All languages for one tokenizer. The corpus is joined with newlines per language."""
    rows = []
    for lang, sents in corpus.items():
        text = "\n".join(sents)
        rows.append(Row(
            tokenizer=tok.key, tokenizer_name=tok.name, used_by=tok.used_by,
            lang=lang, lang_name=names.get(lang, lang), sentences=len(sents),
            chars=len(text), utf8_bytes=len(text.encode("utf-8")), tokens=tok.count(text),
            syllables=count_syllables(text) if lang == TARGET else None,
        ))
    return derive(rows)


def derive(rows: list[Row]) -> list[Row]:
    """Fill in the comparison metrics (mutates and returns rows)."""
    base = {r.tokenizer: r.tokens for r in rows if r.lang == BASELINE}
    for r in rows:
        if r.tokenizer in base and base[r.tokenizer]:
            r.tax = round(r.tokens / base[r.tokenizer], 3)
        r.chars_per_token = round(r.chars / r.tokens, 3) if r.tokens else None
        if r.syllables:
            r.tokens_per_syllable = round(r.tokens / r.syllables, 3)
        if r.tokens:
            r.sentences_in_context = int(CONTEXT / (r.tokens / r.sentences))
    return rows
