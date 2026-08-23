#!/usr/bin/env python3
"""Run the deterministic DocBench matrix with one SSS-delivered Yandex key."""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

from docbench.config import REPO_ROOT, resolve_model
import docbench.run as bench_run


JOBS = (
    ("conformance", REPO_ROOT / "cases" / "seed-grant", "seed-grant"),
    ("rule_extraction", REPO_ROOT / "cases" / "seed-policy", "seed-policy"),
    ("conformance", REPO_ROOT / "cases" / "ace-test", "ace-test"),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-pipe", required=True, type=Path)
    parser.add_argument("--folder-id", required=True)
    parser.add_argument("--out-prefix", default=None)
    args = parser.parse_args()

    secret = args.secret_pipe.read_text(encoding="utf-8").strip()
    if not secret:
        raise RuntimeError("empty decrypted Yandex key")
    os.environ["DOCBENCH_YANDEX_FOLDER_ID"] = args.folder_id
    prefix = args.out_prefix or datetime.now().strftime("yandex-matrix-%Y%m%d-%H%M%S")
    original_resolve = bench_run.resolve_model
    try:
        for model_key in ("yandexgpt-pro-5.1", "yandex-alice-ai-llm"):
            spec = resolve_model(model_key, allow_missing_key=True)
            spec.api_key = secret
            bench_run.resolve_model = lambda requested, allow_missing_key=False, fixed=spec: fixed
            for bench_key, cases_path, cases_label in JOBS:
                out = REPO_ROOT / "var" / "runs" / f"{prefix}-{model_key}-{cases_label}"
                result = bench_run.run_benchmark(
                    bench_key, model_key, cases_path, out_dir=out, max_tokens=8192
                )
                summary = result["summary"]
                print(
                    f"{model_key} {cases_label}: n={summary['n_cases']} "
                    f"scored={summary['n_scored']} errors={summary['n_errors']}"
                )
    finally:
        bench_run.resolve_model = original_resolve
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
