"""Parallel text: the same sentences in every language.

Default source is FLORES-200 (Meta AI, CC BY-SA 4.0): 1,012 "devtest" sentences from
Wikinews/Wikijunior/Wikivoyage, professionally translated into 200 languages. Because
every language has the *same meaning*, token counts are directly comparable.

You can also benchmark your own corpus: a folder with one `<lang>.txt` per language,
line N of each file being a translation of line N of the others.
"""

from __future__ import annotations

import tarfile
import urllib.request
from pathlib import Path

FLORES_URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
CACHE = Path.home() / ".cache" / "myanmar-tokenizer-bench"

# FLORES language codes -> display names. English must stay: it's the 1x baseline.
LANGS = {
    "eng_Latn": "English",
    "mya_Mymr": "Burmese",
    "tha_Thai": "Thai",
    "khm_Khmr": "Khmer",
    "lao_Laoo": "Lao",
    "hin_Deva": "Hindi",
    "vie_Latn": "Vietnamese",
    "zho_Hans": "Chinese (Simplified)",
}
BASELINE = "eng_Latn"
TARGET = "mya_Mymr"


def download_flores(cache: Path = CACHE) -> Path:
    """Download the FLORES-200 archive once (~24 MB)."""
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / "flores200_dataset.tar.gz"
    if archive.exists():
        return archive
    print(f"Downloading FLORES-200 (~24 MB) to {archive} ...")
    part = archive.with_suffix(".part")
    urllib.request.urlretrieve(FLORES_URL, part)
    part.rename(archive)
    return archive


def load_flores(lang: str, split: str = "devtest", cache: Path = CACHE) -> list[str]:
    """Sentences for one language. Extracted files are cached as plain text."""
    out = cache / split / f"{lang}.txt"
    if not out.exists():
        archive = download_flores(cache)
        wanted = f"flores200_dataset/{split}/{lang}.{split}"
        with tarfile.open(archive, "r:gz") as tar:
            # member names may or may not start with "./"
            member = next((m for m in tar.getmembers() if m.name.lstrip("./") == wanted), None)
            f = tar.extractfile(member) if member else None
            if f is None:
                raise FileNotFoundError(f"{wanted} not in FLORES archive")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(f.read())
    return _read_lines(out)


def load_corpus(folder: Path, lang: str) -> list[str]:
    """Sentences from a custom parallel corpus folder (<folder>/<lang>.txt)."""
    return _read_lines(Path(folder) / f"{lang}.txt")


def _read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
