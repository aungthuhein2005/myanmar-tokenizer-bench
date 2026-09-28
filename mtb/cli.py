"""Command line: `mtb run`, `mtb list`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import data
from .bench import Row, measure
from .registry import ALL, API, LOCAL
from .report import write_all


def load_dotenv(path: Path = Path(".env")) -> None:
    """Read KEY=value lines from .env into the environment (existing variables win)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="mtb", description="How many tokens do LLM tokenizers spend on Burmese?")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run the benchmark and write results/")
    run.add_argument("--tokenizers", nargs="*", help=f"keys to run (default: all local). Choices: {', '.join(ALL)}")
    run.add_argument("--api", action="store_true", help="also run API tokenizers (needs ANTHROPIC_API_KEY / GEMINI_API_KEY)")
    run.add_argument("--langs", nargs="*", default=list(data.LANGS), help="FLORES language codes")
    run.add_argument("--split", default="devtest", choices=["dev", "devtest"])
    run.add_argument("--corpus", type=Path, help="custom parallel corpus folder with <lang>.txt files instead of FLORES")
    run.add_argument("--out", type=Path, default=Path("results"))
    run.add_argument("--readme", type=Path, default=Path("README.md"), help="README whose results block to update")

    sub.add_parser("list", help="list available tokenizers")

    rep = sub.add_parser("report", help="rebuild SUMMARY.md, charts and the README block from results/results.json")
    rep.add_argument("--out", type=Path, default=Path("results"))
    rep.add_argument("--readme", type=Path, default=Path("README.md"))
    args = p.parse_args(argv)

    if args.cmd == "list":
        for t in LOCAL + API:
            print(f"{t.key:18} {t.kind:9} {t.name:20} {t.used_by}  [{t.source}]")
        return
    if args.cmd == "report":
        saved = json.loads((args.out / "results.json").read_text(encoding="utf-8"))
        write_all([Row(**r) for r in saved["rows"]], args.out, args.readme, saved["meta"])
        print(f"Rebuilt reports in {args.out}/ from results.json")
        return

    langs = list(dict.fromkeys([data.BASELINE, data.TARGET, *args.langs]))
    load = (lambda lang: data.load_corpus(args.corpus, lang)) if args.corpus else \
           (lambda lang: data.load_flores(lang, args.split))
    corpus = {lang: load(lang) for lang in langs}
    sizes = {len(s) for s in corpus.values()}
    if len(sizes) != 1:
        raise SystemExit(f"Corpus files have different line counts: { {k: len(v) for k, v in corpus.items()} }")

    keys = args.tokenizers or [t.key for t in LOCAL] + ([t.key for t in API] if args.api else [])
    rows = []
    for key in keys:
        tok = ALL[key]
        try:
            print(f"· {tok.name:20}", end=" ", flush=True)
            result = measure(tok, corpus, data.LANGS)
        except Exception as e:  # a gated/missing tokenizer or no API key shouldn't stop the run
            print(f"skipped ({type(e).__name__}: {str(e).splitlines()[0][:100]})")
            continue
        mya = next(r for r in result if r.lang == data.TARGET)
        print(f"Burmese tax {mya.tax:.2f}×")
        rows += result

    if not rows:
        raise SystemExit("No tokenizer ran successfully.")
    meta = {"dataset": f"FLORES-200 {args.split}" if not args.corpus else str(args.corpus),
            "sentences": sizes.pop(), "tokenizers": sorted({r.tokenizer for r in rows})}
    write_all(rows, args.out, args.readme, meta)
    print(f"\nWrote {args.out}/results.csv, results.json, SUMMARY.md and charts.")


if __name__ == "__main__":
    main()
