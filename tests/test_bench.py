from pathlib import Path

from mtb.bench import measure
from mtb.data import load_corpus
from mtb.registry import Tokenizer
from mtb.report import END, START, summary_markdown, write_all
from mtb.syllables import count_syllables, syllables

NAMES = {"eng_Latn": "English", "mya_Mymr": "Burmese", "tha_Thai": "Thai"}


def fake(key: str, per_char: float) -> Tokenizer:
    """Deterministic fake: English at 1 token/4 chars, other scripts at `per_char`."""
    def load():
        def count(text: str) -> int:
            ascii_chars = sum(c.isascii() for c in text)
            return round(ascii_chars / 4 + (len(text) - ascii_chars) * per_char)
        return count
    return Tokenizer(key, key.upper(), "tests", "fake", "fake", load)


CORPUS = {
    "eng_Latn": ["Myanmar is a country in Southeast Asia.", "Bagan has thousands of temples."],
    "mya_Mymr": ["မြန်မာနိုင်ငံသည် အရှေ့တောင်အာရှတွင် ရှိသည်။", "ပုဂံတွင် ဘုရားများစွာ ရှိသည်။"],
    "tha_Thai": ["เมียนมาเป็นประเทศในเอเชียตะวันออกเฉียงใต้", "พุกามมีวัดหลายพันแห่ง"],
}


def test_syllables():
    assert syllables("မြန်မာနိုင်ငံ") == ["မြန်", "မာ", "နိုင်", "ငံ"]
    assert syllables("ကမ္ဘာ") == ["ကမ္ဘာ"]
    assert count_syllables("ပုဂံ။") == 2  # punctuation not counted


def test_measure_and_tax():
    rows = measure(fake("a", 1.0), CORPUS, NAMES)
    by = {r.lang: r for r in rows}
    assert by["eng_Latn"].tax == 1.0
    assert by["mya_Mymr"].tax > 1
    assert by["mya_Mymr"].syllables and by["mya_Mymr"].tokens_per_syllable
    assert by["tha_Thai"].syllables is None
    assert by["mya_Mymr"].sentences_in_context < by["eng_Latn"].sentences_in_context


def test_summary_orders_best_first():
    rows = measure(fake("good", 0.5), CORPUS, NAMES) + measure(fake("bad", 2.0), CORPUS, NAMES)
    md = summary_markdown(rows, {"dataset": "test", "sentences": 2, "date": "2026-01-01"})
    assert md.index("| GOOD |") < md.index("| BAD |")
    assert "Burmese needs" in md


def test_write_all_updates_readme(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(f"intro\n{START}\nOLD_BLOCK\n{END}\noutro\n", encoding="utf-8")
    rows = measure(fake("a", 1.0), CORPUS, NAMES)
    write_all(rows, tmp_path / "results", readme, {"dataset": "test", "sentences": 2})
    for f in ("results.csv", "results.json", "SUMMARY.md", "burmese_tax_light.png", "burmese_tax_dark.png"):
        assert (tmp_path / "results" / f).exists(), f
    text = readme.read_text(encoding="utf-8")
    assert "OLD_BLOCK" not in text and "Burmese needs" in text and text.endswith("outro\n")


def test_custom_corpus(tmp_path: Path):
    (tmp_path / "mya_Mymr.txt").write_text("ပုဂံ\n\nမြန်မာ\n", encoding="utf-8")
    assert load_corpus(tmp_path, "mya_Mymr") == ["ပုဂံ", "မြန်မာ"]
