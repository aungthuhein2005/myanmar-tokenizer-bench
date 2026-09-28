"""Build report.pdf ("Burmese pays more than its neighbours") from results/results.json.

    python scripts/make_report.py

Writes charts to results/report/, an HTML version, and report.pdf (printed with headless
Chromium via Playwright, which shapes Burmese script correctly).
"""

from __future__ import annotations

import html
import json
import statistics as st
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mtb.bench import Row  # noqa: E402
from mtb.chart import _bar  # noqa: E402
from mtb.registry import ALL  # noqa: E402
from mtb.report import same_tokenizer_groups  # noqa: E402

ASSETS = ROOT / "results" / "report"
AUTHOR = "Aung Thu Hein"
TITLE = "Burmese pays more than its neighbours"
REPO = "github.com/aungthuhein2005/myanmar-tokenizer-bench"

# Chart ink (light theme, print)
SURFACE, INK, INK2, MUTED, GRID, BASE = "#ffffff", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#b4b2aa"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
FONT = ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]

LANGS = ["Burmese", "Thai", "Khmer", "Lao", "Hindi", "Vietnamese", "Chinese (Simplified)"]
SHORT = {  # display names for tokenizers that several models share
    "OpenAI o200k": "GPT-4o to GPT-6 (o200k)",
    "OpenAI cl100k": "GPT-4 / GPT-3.5 (cl100k)",
    "Gemma 3": "Gemini / Gemma 3",
    "Claude Opus 5": "Claude Opus 5 / Sonnet 5",
}


# ---------------------------------------------------------------- data

def load():
    saved = json.loads((ROOT / "results" / "results.json").read_text(encoding="utf-8"))
    rows = [Row(**r) for r in saved["rows"]]
    groups = same_tokenizer_groups(rows)
    primary = {g[0]: g for g in groups}
    tax: dict[str, dict[str, float]] = {}
    tokens: dict[str, dict[str, int]] = {}
    for r in rows:
        if r.tokenizer_name in primary:
            tax.setdefault(r.tokenizer_name, {})[r.lang_name] = r.tax
            tokens.setdefault(r.tokenizer_name, {})[r.lang_name] = r.tokens
    return saved["meta"], rows, primary, tax, tokens


def label(name: str) -> str:
    return SHORT.get(name, name)


# ---------------------------------------------------------------- charts

def _style(ax):
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(BASE)
    ax.tick_params(axis="y", length=0, pad=8, labelsize=9.5, colors=INK2)
    ax.tick_params(axis="x", length=0, labelsize=8.5, colors=MUTED)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def _fig(h: float, w: float = 8.0):
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = FONT
    fig, ax = plt.subplots(figsize=(w, h), dpi=220)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    return fig, ax


def chart_median(tax, out: Path) -> dict[str, float]:
    med = {lang: st.median(tax[t][lang] for t in tax) for lang in LANGS}
    order = sorted(med, key=med.get)  # barh: bottom-up, most expensive on top
    fig, ax = _fig(3.0)
    span = max(med.values()) * 1.15
    for i, lang in enumerate(order):
        color = BLUE if lang == "Burmese" else GRAY
        _bar(ax, i, med[lang], 0.52, span * 0.008, color)
        ax.text(med[lang] + 0.08, i, f"{med[lang]:.1f}×", va="center", fontsize=9.5,
                color=INK, fontweight="semibold" if lang == "Burmese" else "normal")
    ax.set_yticks(range(len(order)), order)
    for tick in ax.get_yticklabels():
        if tick.get_text() == "Burmese":
            tick.set_color(INK)
            tick.set_fontweight("bold")
    ax.axvline(1, color=MUTED, linewidth=1, zorder=2)
    ax.text(1.04, len(order) - 0.45, "English = 1×", color=MUTED, fontsize=8, va="bottom")
    ax.set_xlim(0, max(med.values()) * 1.15)
    ax.set_ylim(-0.6, len(order) - 0.2)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:g}×")
    _style(ax)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return med


def chart_dumbbell(tax, out: Path) -> None:
    names = sorted(tax, key=lambda t: tax[t]["Burmese"])  # bottom-up: worst on top
    fig, ax = _fig(0.9 + 0.3 * len(names))
    xmax = max(tax[t]["Burmese"] for t in tax) * 1.28
    for i, t in enumerate(names):
        b, th = tax[t]["Burmese"], tax[t]["Thai"]
        ax.plot([th, b], [i, i], color=GRID, linewidth=2.2, zorder=2, solid_capstyle="round")
        ax.scatter([th], [i], s=58, color=ORANGE, zorder=3, edgecolors=SURFACE, linewidths=1.2)
        ax.scatter([b], [i], s=58, color=BLUE, zorder=4, edgecolors=SURFACE, linewidths=1.2)
        ax.text(xmax, i, f"{b / th:.1f}× Thai", va="center", ha="right", fontsize=8.5, color=INK2)
    top = len(names) - 1
    ax.annotate("Burmese", (tax[names[top]]["Burmese"], top), xytext=(0, 9), textcoords="offset points",
                ha="center", fontsize=8.5, color=INK, fontweight="semibold")
    ax.annotate("Thai", (tax[names[top]]["Thai"], top), xytext=(0, 9), textcoords="offset points",
                ha="center", fontsize=8.5, color=INK, fontweight="semibold")
    ax.set_yticks(range(len(names)), [label(t) for t in names])
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, len(names) - 0.05)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:g}×")
    _style(ax)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=BLUE, markersize=7, label="Burmese"),
                       plt.Line2D([], [], marker="o", ls="", color=ORANGE, markersize=7, label="Thai")],
              loc="lower right", bbox_to_anchor=(1, 1.0), ncol=2, frameon=False, fontsize=8.5,
              labelcolor=INK2, handletextpad=0.4, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def chart_heatmap(tax, out: Path) -> None:
    names = sorted(tax, key=lambda t: tax[t]["Burmese"])[::-1]  # most expensive for Burmese first
    data = [[tax[t][lang] for lang in LANGS] for t in names]
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    norm = LogNorm(vmin=1, vmax=15)
    fig, ax = _fig(0.7 + 0.28 * len(names))
    ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            dark = norm(max(v, 1)) > 0.5
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8.5,
                    color="#ffffff" if dark else INK, fontweight="bold" if j == 0 else "normal")
    ax.set_xticks(range(len(LANGS)), ["Chinese" if lang.startswith("Chinese") else lang for lang in LANGS],
                  fontsize=9, color=INK2)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(names)), [label(t) for t in names], fontsize=9, color=INK2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([x - 0.5 for x in range(1, len(LANGS))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(names))], minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    ax.add_patch(plt.Rectangle((-0.5, -0.5), 1, len(names), fill=False, edgecolor=INK, linewidth=1.6))
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def chart_providers(tokens, out: Path) -> None:
    keep = ["Gemma 3", "OpenAI o200k", "Claude Opus 5", "Claude Haiku 4.5"]
    names = sorted([k for k in keep if k in tokens], key=lambda t: tokens[t]["Burmese"])
    fig, ax = _fig(0.7 + 0.42 * len(names))
    for i, t in enumerate(names):
        ax.barh(i - 0.14, tokens[t]["English"] / 1000, height=0.26, color=GRAY, zorder=3)
        ax.barh(i + 0.14, tokens[t]["Burmese"] / 1000, height=0.26, color=BLUE, zorder=3)
        ax.text(tokens[t]["Burmese"] / 1000 + 2, i + 0.14, f"{tokens[t]['Burmese'] / 1000:.0f}K",
                va="center", fontsize=8.5, color=INK, fontweight="semibold")
        ax.text(tokens[t]["English"] / 1000 + 2, i - 0.14, f"{tokens[t]['English'] / 1000:.0f}K",
                va="center", fontsize=8, color=INK2)
    ax.set_yticks(range(len(names)), [label(t) for t in names])
    ax.set_xlim(0, max(tokens[t]["Burmese"] for t in names) / 1000 * 1.15)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:g}K")
    _style(ax)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Burmese"),
                       plt.Rectangle((0, 0), 1, 1, color=GRAY, label="English")],
              loc="lower right", bbox_to_anchor=(1, 1.0), ncol=2, frameon=False, fontsize=8.5,
              labelcolor=INK2, handletextpad=0.4, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------- example word

def word_example() -> list[tuple[str, int]]:
    word = "မြန်မာ"
    out = []
    for key, name in [("cl100k", "GPT-4 (cl100k)"), ("qwen3", "Qwen 3"), ("o200k", "GPT-4o to GPT-6"),
                      ("gemma3", "Gemini / Gemma 3"), ("nllb", "NLLB-200")]:
        try:
            out.append((name, ALL[key].count(word)))
        except Exception:  # tokenizer not available offline
            pass
    return out


# ---------------------------------------------------------------- page

CSS = """
@page { size: A4; margin: 16mm 16mm 18mm; }
* { box-sizing: border-box; }
body { margin: 0; color: #1c1917; font: 10pt/1.55 "Segoe UI", "Helvetica Neue", Arial, "Myanmar Text", "Noto Sans Myanmar", sans-serif; }
.my { font-family: "Myanmar Text", "Noto Sans Myanmar", sans-serif; line-height: 1.9; }
.kicker { font-size: 8.5pt; letter-spacing: .08em; text-transform: uppercase; color: #0b6b63; font-weight: 700; }
h1 { font-size: 27pt; line-height: 1.12; margin: 6pt 0 8pt; letter-spacing: -.01em; }
.dek { font-size: 12pt; color: #44403c; margin: 0 0 14pt; max-width: 150mm; }
h2 { font-size: 14pt; margin: 18pt 0 4pt; color: #0b0b0b; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 12pt 0 2pt; break-after: avoid; }
p { margin: 0 0 7pt; }
.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8pt; margin: 4pt 0 10pt; }
.tile { border: 1px solid #e7e2da; border-radius: 8pt; padding: 9pt 11pt; background: #faf8f5; }
.tile .v { font-size: 22pt; font-weight: 700; color: #0b6b63; line-height: 1.1; }
.byline { font-size: 9.5pt; color: #57534e; margin: 0 0 10pt; }
.byline b { color: #1c1917; font-weight: 600; }
.tile .l { font-size: 8.5pt; color: #57534e; line-height: 1.35; margin-top: 3pt; }
figure { margin: 6pt 0 10pt; break-inside: avoid; }
figure img { width: 100%; display: block; }
figcaption { font-size: 8.5pt; color: #6b6660; margin-top: 3pt; }
.fig-title { font-weight: 700; font-size: 10.5pt; margin-bottom: 1pt; }
.fig-sub { font-size: 8.5pt; color: #6b6660; margin-bottom: 4pt; }
.callout { border-left: 3pt solid #f8b82d; background: #fdf6e3; padding: 7pt 11pt; border-radius: 0 6pt 6pt 0; margin: 8pt 0 10pt; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 4pt 0 10pt; break-inside: avoid; }
th, td { padding: 4pt 6pt; border-bottom: 1px solid #ebe7e0; text-align: left; }
th { font-weight: 600; color: #57534e; font-size: 8.5pt; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
ul { margin: 0 0 8pt; padding-left: 14pt; } li { margin: 2pt 0; }
.page { break-before: page; }
.small { font-size: 8.5pt; color: #57534e; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f3f0eb; padding: 0 3pt; border-radius: 3pt; }
"""


def build_html(meta, tax, tokens, med, words) -> str:
    n = len(tax)
    bur_thai = st.mean(tax[t]["Burmese"] / tax[t]["Thai"] for t in tax)
    most_exp = sum(max(tax[t], key=tax[t].get) == "Burmese" for t in tax)
    beats = {lang: sum(tax[t]["Burmese"] > tax[t][lang] for t in tax) for lang in LANGS[1:]}
    worst = max(tax, key=lambda t: tax[t]["Burmese"])
    best_chat = min((t for t in tax if t != "NLLB-200"), key=lambda t: tax[t]["Burmese"])
    rank = sorted(med, key=med.get, reverse=True)
    esc = html.escape
    sent = f"{meta['sentences']:,}"

    word_head = "".join(f"<th class='n'>{esc(nm)}</th>" for nm, _ in words)
    word_cells = "".join(f"<td class='n'><b>{c}</b></td>" for _, c in words)
    prov = [t for t in ["Gemma 3", "OpenAI o200k", "Claude Opus 5", "Claude Haiku 4.5"] if t in tokens]
    prov_rows = "".join(
        f"<tr><td>{esc(label(t))}</td><td class='n'>{tokens[t]['English']:,}</td>"
        f"<td class='n'><b>{tokens[t]['Burmese']:,}</b></td><td class='n'>{tax[t]['Burmese']:.1f}×</td></tr>"
        for t in sorted(prov, key=lambda t: tokens[t]["Burmese"]))

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="author" content="{esc(AUTHOR)}"><title>{esc(TITLE)}</title>
<style>{CSS}</style></head><body>

<div class="kicker">myanmar-tokenizer-bench · Report · {date.today():%B %Y}</div>
<h1>Burmese pays more than its neighbours</h1>
<p class="byline">By <b>{esc(AUTHOR)}</b> · {date.today().day} {date.today():%B %Y}</p>
<p class="dek">AI models charge by the token. We counted how many tokens {n} tokenizers, used by GPT, Claude,
Gemini, Llama, Qwen and others, need for the same {sent} sentences in English, Burmese and six other Asian languages.</p>

<div class="tiles">
  <div class="tile"><div class="v">{bur_thai:.1f}×</div><div class="l">Burmese costs this much more than Thai for the same meaning, on average (it's costlier with all {n} tokenizers)</div></div>
  <div class="tile"><div class="v">{most_exp} of {n}</div><div class="l">tokenizers make Burmese the most expensive of all seven languages tested</div></div>
  <div class="tile"><div class="v">{tax[worst]['Burmese']:.1f}×</div><div class="l">English, the worst case ({esc(label(worst))}), close to one token per byte of text</div></div>
</div>

<figure>
  <div class="fig-title">Median token cost relative to English</div>
  <div class="fig-sub">Tokens for the same {sent} FLORES-200 sentences ÷ tokens for English, median of {n} distinct tokenizers</div>
  <img src="median.png" alt="Median token cost by language: {', '.join(f'{lang} {med[lang]:.1f}×' for lang in rank)}">
</figure>

<p>Across the region, Burmese sits in the expensive group. With the typical tokenizer it needs
<b>{med['Burmese']:.1f}×</b> the tokens of English, twice Thai ({med['Thai']:.1f}×) and Hindi ({med['Hindi']:.1f}×), and far
more than Vietnamese ({med['Vietnamese']:.1f}×) or Chinese ({med['Chinese (Simplified)']:.1f}×).
It is costlier than Thai, Hindi, Vietnamese and Chinese with <b>every</b> tokenizer we tested.</p>

<div class="callout"><b>One honest caveat.</b> Burmese isn't the only language paying this tax. Lao
({med['Lao']:.1f}×) and Khmer ({med['Khmer']:.1f}×) have even higher medians, and Burmese beats them with only
{beats['Lao']} and {beats['Khmer']} of {n} tokenizers respectively. The pattern is about <i>scripts with little
training data</i>, and Burmese is one of the hardest hit.</div>

<div class="page"></div>
<h2>Burmese vs Thai: same region, very different bills</h2>
<p>Thai is the fairest comparison: a Southeast Asian language with its own script and no spaces between words,
just like Burmese. Yet every tokenizer is kinder to Thai, and the gap is widest for older and English- or
Chinese-centred vocabularies: with Llama 3, Burmese costs <b>{tax['Llama 3']['Burmese'] / tax['Llama 3']['Thai']:.1f}×</b>
as much as Thai; with Qwen 3, <b>{tax['Qwen 3']['Burmese'] / tax['Qwen 3']['Thai']:.1f}×</b>. Only NLLB-200, a translation
model built for 200 languages, treats the two almost equally.</p>
<figure>
  <div class="fig-title">Tokens relative to English, Burmese vs Thai</div>
  <div class="fig-sub">Each row is one tokenizer; the label on the right shows how many times more Burmese costs than Thai</div>
  <img src="dumbbell.png" alt="Dumbbell chart comparing Burmese and Thai token cost for each tokenizer">
</figure>

<h2>All languages, all tokenizers</h2>
<figure>
  <div class="fig-sub">Tokens relative to English (1.0 = same as English). Darker = more expensive. Burmese column outlined.</div>
  <img src="heatmap.png" alt="Heatmap of token cost relative to English for each tokenizer and language">
</figure>

<div class="page"></div>
<h2>What it means for the bill</h2>
<p>The multiplier compares a tokenizer with itself. To compare <b>providers</b>, count the absolute tokens for the
same text: that's what you pay for (times each provider's price per token).</p>
<figure>
  <div class="fig-title">Tokens for the same {sent} sentences</div>
  <div class="fig-sub">Thousands of tokens, English vs Burmese, for the three major API providers' current tokenizers</div>
  <img src="providers.png" alt="Bar chart of English and Burmese token counts for Gemini, GPT and Claude">
</figure>
<table><tr><th>Tokenizer</th><th class="n">English tokens</th><th class="n">Burmese tokens</th><th class="n">Burmese ÷ English</th></tr>{prov_rows}</table>
<p>Gemini needs the fewest tokens for Burmese. Claude needs about <b>{tokens['Claude Opus 5']['Burmese'] / tokens['OpenAI o200k']['Burmese']:.1f}×</b>
as many as GPT and <b>{tokens['Claude Opus 5']['Burmese'] / tokens['Gemma 3']['Burmese']:.1f}×</b> as many as Gemini. Claude's newer
tokenizer (Opus 5 / Sonnet 5) shows a lower multiplier than Haiku 4.5 only because it uses more tokens for English; for
Burmese the two are almost identical.</p>

<h2>Why it happens</h2>
<p>Tokenizers learn their vocabulary from training data that is mostly English, code and a few large languages. A
script that is rare in that data gets few dedicated tokens, so its text is split into small fragments, down to raw
UTF-8 bytes. Each Burmese character takes 3 bytes, so byte-level fallback is especially costly. The word
<span class="my">မြန်မာ</span> ("Myanmar"), 6 characters and 18 bytes, needs:</p>
<table><tr><th>Tokenizer</th>{word_head}</tr><tr><td>Tokens for <span class="my">မြန်မာ</span></td>{word_cells}</tr></table>

<h2>What Burmese developers can do</h2>
<ul>
  <li><b>Pick the tokenizer, not just the model.</b> For Burmese-heavy workloads, {esc(label(best_chat))} needs
  {tax[best_chat]['Burmese']:.1f}× English against {tax[worst]['Burmese']:.1f}× for {esc(label(worst))}. That gap is money, latency and context.</li>
  <li><b>Budget context in Burmese tokens.</b> A 128K window holds roughly {int(128000 / (tokens[worst]['Burmese'] / meta['sentences'])):,}
  Burmese sentences with {esc(label(worst))}, against {int(128000 / (tokens[worst]['English'] / meta['sentences'])):,} in English.</li>
  <li><b>Chunk by syllables, not characters,</b> when building retrieval systems, so chunks stay even in meaning
  (see <i>Burmese RAG</i>).</li>
  <li><b>Measure your own text.</b> Run <code>mtb run --corpus your_folder/</code> on your real documents.</li>
</ul>

<h2>Method and limitations</h2>
<p class="small">Data: FLORES-200 devtest ({sent} sentences from Wikinews, Wikijunior and Wikivoyage, professionally translated;
CC BY-SA 4.0). Each language's sentences are joined by newlines and tokenized without special tokens. The multiplier is
tokens(language) ÷ tokens(English) for the same tokenizer. Models whose counts are identical in every language share a
tokenizer and are counted once ({n} distinct tokenizers): GPT-5, GPT-5.5, GPT-6 Sol and Phi-4 mini match o200k;
Gemini 2.5 and 3.8 Flash match Gemma 3; Claude Sonnet 5 matches Opus 5. Claude, GPT-5+ and Gemini were counted with their
official token-counting APIs, with the fixed message framing subtracted; Llama 3, Gemma 3 and Mistral tokenizers come from
public mirrors of the official files. Limitations: news and wiki text only; Unicode Burmese only (Zawgyi not measured);
token efficiency is not answer quality; provider tokenizers can change with new models. Run date: {meta['date']}.</p>
<p class="small">Code and full data: <b>{REPO}</b> (MIT).</p>
</body></html>"""


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    meta, _, _, tax, tokens = load()
    med = chart_median(tax, ASSETS / "median.png")
    chart_dumbbell(tax, ASSETS / "dumbbell.png")
    chart_heatmap(tax, ASSETS / "heatmap.png")
    chart_providers(tokens, ASSETS / "providers.png")
    page = ASSETS / "report.html"
    page.write_text(build_html(meta, tax, tokens, med, word_example()), encoding="utf-8")

    from playwright.sync_api import sync_playwright

    footer = ("<div style='width:100%;font:7.5pt Segoe UI,Arial;color:#8a847d;padding:0 16mm;display:flex;"
              f"justify-content:space-between'><span>{TITLE} · {AUTHOR} · myanmar-tokenizer-bench"
              "</span><span><span class='pageNumber'></span> / <span class='totalPages'></span></span></div>")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(page.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.pdf(path=str(ROOT / "report.pdf"), format="A4", print_background=True,
               display_header_footer=True, header_template="<div></div>", footer_template=footer,
               margin={"top": "16mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
        browser.close()

    # Document properties (Chromium doesn't set an author)
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter(clone_from=PdfReader(ROOT / "report.pdf"))
    writer.add_metadata({"/Title": TITLE, "/Author": AUTHOR,
                         "/Subject": "How many tokens LLM tokenizers spend on Burmese vs neighbouring languages",
                         "/Keywords": "Burmese, Myanmar, tokenizer, LLM, benchmark"})
    with open(ROOT / "report.pdf", "wb") as f:
        writer.write(f)
    print(f"wrote {ROOT / 'report.pdf'}")


if __name__ == "__main__":
    main()
