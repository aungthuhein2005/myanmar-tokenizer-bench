"""Write results: raw CSV/JSON, a Markdown summary, the charts, and the README results block."""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path

from .bench import CONTEXT, Row
from .chart import bar_chart
from .data import BASELINE, TARGET

START, END = "<!-- results:start -->", "<!-- results:end -->"


def _by(rows: list[Row], lang: str) -> dict[str, Row]:
    return {r.tokenizer: r for r in rows if r.lang == lang}


def same_tokenizer_groups(rows: list[Row]) -> list[list[str]]:
    """Tokenizer names grouped by identical token counts in every language (= same tokenizer)."""
    counts: dict[str, list[tuple[str, int]]] = {}
    names: dict[str, str] = {}
    for r in rows:
        counts.setdefault(r.tokenizer, []).append((r.lang, r.tokens))
        names[r.tokenizer] = r.tokenizer_name
    groups: dict[tuple, list[str]] = {}
    for key, c in counts.items():
        groups.setdefault(tuple(sorted(c)), []).append(names[key])
    return list(groups.values())


def summary_markdown(rows: list[Row], meta: dict) -> str:
    mya, eng = _by(rows, TARGET), _by(rows, BASELINE)
    order = sorted(mya, key=lambda k: mya[k].tax or 0)
    langs = list(dict.fromkeys(r.lang for r in rows if r.lang != BASELINE))
    names = {r.lang: r.lang_name for r in rows}
    best, worst = mya[order[0]], mya[order[-1]]

    out = [
        f"_Dataset: {meta['dataset']} · {meta['sentences']} parallel sentences · run {meta['date']}_",
        "",
        f"**Burmese needs {best.tax:.1f}× to {worst.tax:.1f}× as many tokens as English** for the same "
        f"sentences. With the least efficient tokenizer ({worst.tokenizer_name}), the same Burmese text "
        f"costs {worst.tax:.1f}× more, runs about {worst.tax:.1f}× slower to generate, and a "
        f"{CONTEXT // 1000}K context window holds {worst.sentences_in_context:,} Burmese sentences "
        f"instead of {eng[worst.tokenizer].sentences_in_context:,} English ones.",
        "",
        "### Burmese vs English",
        "",
        "| Tokenizer | Used by | English tokens | Burmese tokens | Burmese tax | Tokens / syllable | Sentences in 128K (Burmese / English) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for k in order:
        m, e = mya[k], eng[k]
        out.append(
            f"| {m.tokenizer_name} | {m.used_by} | {e.tokens:,} | {m.tokens:,} | **{m.tax:.2f}×** | "
            f"{m.tokens_per_syllable:.2f} | {m.sentences_in_context:,} / {e.sentences_in_context:,} |"
        )

    shared = [g for g in same_tokenizer_groups(rows) if len(g) > 1]
    if shared:
        out += ["", "Identical counts in every language, so these share one tokenizer: "
                + "; ".join(" = ".join(g) for g in shared) + "."]

    out += ["", "### Every language (tokens as a multiple of English)", "",
            "| Tokenizer | " + " | ".join(names[lang] for lang in langs) + " |",
            "|---|" + "---:|" * len(langs)]
    table = {(r.tokenizer, r.lang): r for r in rows}
    for k in order:
        cells = []
        for lang in langs:
            r = table.get((k, lang))
            cell = f"{r.tax:.2f}×" if r and r.tax else "–"
            cells.append(f"**{cell}**" if lang == TARGET else cell)
        out.append(f"| {mya[k].tokenizer_name} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def write_all(rows: list[Row], out_dir: Path, readme: Path | None, meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {**meta, "date": meta.get("date") or date.today().isoformat()}

    with (out_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].to_dict()))
        w.writeheader()
        w.writerows(r.to_dict() for r in rows)
    (out_dir / "results.json").write_text(
        json.dumps({"meta": meta, "rows": [r.to_dict() for r in rows]}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    md = summary_markdown(rows, meta)
    (out_dir / "SUMMARY.md").write_text("# Results\n\n" + md, encoding="utf-8")

    # One bar per distinct tokenizer: models with identical counts share a bar.
    mya = _by(rows, TARGET)
    bars = []
    for names in same_tokenizer_groups(rows):
        r = next(m for m in mya.values() if m.tokenizer_name == names[0])
        label = names[0] if len(names) == 1 else f"{names[0]}\n= {', '.join(names[1:])}"
        bars.append((label, r.tax, r.tokens))
    base = f"Same {meta['sentences']:,} {meta['dataset']} sentences"
    for theme in ("light", "dark"):
        bar_chart([(lbl, tax) for lbl, tax, _ in bars], out_dir / f"burmese_tax_{theme}.png", theme,
                  title="How many tokens Burmese costs compared with English",
                  subtitle=f"{base} · tokens(Burmese) ÷ tokens(English) · lower is better",
                  fmt="{:.1f}×", reference=(1, "English = 1×"))
        bar_chart([(lbl, n / 1000) for lbl, _, n in bars], out_dir / f"burmese_tokens_{theme}.png", theme,
                  title="Tokens needed for the same Burmese text",
                  subtitle=f"{base} in Burmese · thousands of tokens · lower is cheaper",
                  fmt="{:.0f}K", reference=None)

    if readme and readme.exists():
        text = readme.read_text(encoding="utf-8")
        if START in text and END in text:
            block = f"{START}\n{md}{END}"
            readme.write_text(re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: block, text, flags=re.S),
                              encoding="utf-8")
