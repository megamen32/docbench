#!/usr/bin/env python3
"""Publish the Russian supplementary campaign with the standard Pages UI."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from docbench.leaderboard import publish_pages


RUSSIAN_SUITES = {
    "datasets/russian/grant/cases": ("Грантовые заявки", 10),
    "datasets/russian/policy/cases": ("Извлечение правил из русских политик", 12),
    "datasets/russian/ace/cases": ("Договоры ACE", 30),
}


def publish(campaign_dir: Path, output: Path) -> dict:
    """Replace only generated run cards, then reuse the canonical Pages renderer."""
    runs = output / "runs"
    if runs.exists():
        shutil.rmtree(runs)
    return publish_pages(campaign_dir, output, suites=RUSSIAN_SUITES)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.campaign_dir, args.out)
    print(result["out"])
