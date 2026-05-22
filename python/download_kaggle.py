"""Download the IBM Credit Card Transactions dataset from Kaggle.

Requires the Kaggle CLI to be configured (~/.kaggle/kaggle.json).
Falls back to a clear message if the dataset slug has changed — the IBM
synthetic data has been re-uploaded under several owners over time.

If you cannot get Kaggle access, run python/generate_data.py instead to
produce a synthetic-but-schema-identical local dataset.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# Common slugs observed for this dataset on Kaggle:
CANDIDATES = [
    "ealaxi/paysim1",  # similar synthetic
    "ealaxi/credit-card-transactions",
    "computingvictor/transactions-fraud-datasets",
]


def try_download(slug: str) -> bool:
    try:
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", slug, "-p", str(RAW), "--unzip"],
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main() -> int:
    for slug in CANDIDATES:
        print(f"trying {slug}...")
        if try_download(slug):
            print(f"downloaded {slug} into {RAW}")
            return 0
    print(
        "Kaggle download failed. Either the slug has changed or the Kaggle CLI "
        "is not configured. Run `python python/generate_data.py` to produce a "
        "schema-identical synthetic dataset locally.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
