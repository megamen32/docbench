"""docbench CLI: run, errorgen, datasets, models, report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import REPO_ROOT, list_models


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="docbench", description=__doc__)
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run a benchmark on a model")
    p_run.add_argument("--bench", required=True, choices=["conformance", "rule_extraction"])
    p_run.add_argument("--model", required=True)
    p_run.add_argument("--cases", required=True, help="case yaml file or directory")
    p_run.add_argument("--ruleset-dir", default=str(REPO_ROOT / "rulesets"))
    p_run.add_argument("--ruleset", default=None, help="override ruleset id for conformance")
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--offline", action="store_true",
                       help="serve from response cache only; error on cache miss")
    p_run.add_argument("--out", default=None, help="output dir (default var/runs/<ts>-…)")
    p_run.add_argument("--max-tokens", type=int, default=8192)

    p_gen = sub.add_parser("errorgen", help="apply a corruption plan to a valid packet")
    p_gen.add_argument("--plan", required=True, help="errorgen plan yaml")
    p_gen.add_argument("--cases-dir", default=str(REPO_ROOT / "cases"))
    p_gen.add_argument("--out", required=True, help="output dir for corrupted cases")

    p_ds = sub.add_parser("datasets", help="dataset sidecar")
    p_ds_sub = p_ds.add_subparsers(dest="ds_cmd", required=True)
    p_list = p_ds_sub.add_parser("list", help="list registry entries and local state")
    p_fetch = p_ds_sub.add_parser("fetch", help="download datasets")
    p_fetch.add_argument("--only", action="append", default=None)
    p_fetch.add_argument("--all", action="store_true")
    p_fetch.add_argument("--min-free-gb", type=float, default=30.0)

    p_models = sub.add_parser("models", help="list configured models")

    p_report = sub.add_parser("report", help="merge run results into one markdown report")
    p_report.add_argument("runs", nargs="+", help="results.json files or run dirs")
    p_report.add_argument("--out", default=None)

    args = ap.parse_args(argv)

    if args.cmd == "run":
        from .run import run_benchmark
        res = run_benchmark(
            args.bench, args.model, Path(args.cases),
            ruleset_dir=Path(args.ruleset_dir), ruleset_id=args.ruleset,
            limit=args.limit, offline=args.offline,
            out_dir=Path(args.out) if args.out else None,
            max_tokens=args.max_tokens,
        )
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
        print("results:", res["out_dir"])
        return 0

    if args.cmd == "errorgen":
        from .errorgen import apply_plan
        written = apply_plan(Path(args.plan), Path(args.cases_dir), Path(args.out))
        for w in written:
            print("wrote", w)
        return 0

    if args.cmd == "datasets":
        from .datasets import registry_entries, fetch_entry, local_state
        entries = registry_entries()
        if args.ds_cmd == "list":
            for e in entries:
                st = local_state(e)
                print(f"{e['name']:<22} {e['source_type']:<8} {e.get('repo_id') or e.get('url', ''):<55} "
                      f"[{st}] {e.get('notes', '')}")
            return 0
        if args.ds_cmd == "fetch":
            sel = [e for e in entries if args.all or e["name"] in (args.only or [])]
            if not sel:
                print("no matching datasets", file=sys.stderr)
                return 2
            rc = 0
            for e in sel:
                try:
                    fetch_entry(e, min_free_gb=args.min_free_gb)
                except Exception as ex:
                    print(f"FAIL {e['name']}: {ex}", file=sys.stderr)
                    rc = 1
            return rc

    if args.cmd == "models":
        for m in list_models():
            price = f"${m.price_in}/${m.price_out} per 1M" if m.price_in is not None else "no price"
            print(f"{m.key:<26} {m.alias:<28} {m.provider:<10} {price}"
                  + ("" if m.api_key else "  [NO KEY]"))
        return 0

    if args.cmd == "report":
        from .run import render_markdown_report
        results = []
        for r in args.runs:
            p = Path(r)
            f = p / "results.json" if p.is_dir() else p
            results.append(json.loads(Path(f).read_text(encoding="utf-8")))
        md = render_markdown_report(results)
        if args.out:
            Path(args.out).write_text(md, encoding="utf-8")
            print("wrote", args.out)
        else:
            print(md)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
