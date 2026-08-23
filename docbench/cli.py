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
    p_run.add_argument("--bench", required=True, choices=["conformance", "rule_extraction", "iri_review"])
    p_run.add_argument("--model", required=True)
    p_run.add_argument("--cases", required=True, help="case yaml file or directory")
    p_run.add_argument("--ruleset-dir", default=str(REPO_ROOT / "rulesets"))
    p_run.add_argument("--ruleset", default=None, help="override ruleset id for conformance")
    p_run.add_argument("--gold", default=None,
                       help="private gold YAML for iri_review; keep it outside the repository")
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--offline", action="store_true",
                       help="serve from response cache only; error on cache miss")
    p_run.add_argument("--out", default=None, help="output dir (default var/runs/<ts>-…)")
    p_run.add_argument("--max-tokens", type=int, default=8192)
    p_run.add_argument("--effort", default=None,
                       help="reasoning effort label from docbench/models.yaml "
                            "(e.g. thinking / no_thinking); default from catalog")
    p_run.add_argument("--locale", choices=["en", "ru"], default="en",
                       help="language of benchmark instructions; case data is unchanged")
    p_run.add_argument("--dataset-version", default=None,
                       help="explicit dataset version recorded in results.json")
    p_run.add_argument("--usd-rub", type=float, default=None,
                       help="pinned USD/RUB rate; requires --fx-date")
    p_run.add_argument("--fx-date", default=None,
                       help="date for --usd-rub (YYYY-MM-DD)")
    p_run.add_argument("--allow-repeat", action="store_true",
                       help="permit a new provider call despite an equivalent complete cache-cold run")
    p_run.add_argument("--repeat-label", default=None,
                       help="required label for an intentional repeat, e.g. variance-2-of-3")

    p_campaign = sub.add_parser(
        "campaign", help="run selected models consistently across the standard document suites")
    p_campaign.add_argument("--models", nargs="+", required=True)
    p_campaign.add_argument("--suite", dest="suites", action="append",
                            choices=["grant", "policy", "ace"],
                            help="repeat to select suites; default: grant, policy, ace")
    p_campaign.add_argument("--offline", action="store_true",
                            help="serve from response cache only; requires --usd-rub and --fx-date")
    p_campaign.add_argument("--out", default=None, help="campaign output root")
    p_campaign.add_argument("--limit", type=int, default=None)
    p_campaign.add_argument("--max-tokens", type=int, default=8192)
    p_campaign.add_argument("--usd-rub", type=float, default=None,
                            help="pinned USD/RUB rate; otherwise fetch CBR once at campaign start")
    p_campaign.add_argument("--fx-date", default=None,
                            help="date for --usd-rub (YYYY-MM-DD)")

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

    p_conv = sub.add_parser("convert", help="convert an external dataset into docbench cases")
    p_conv.add_argument("--source", required=True, choices=["ace"])
    p_conv.add_argument("--input",
                        default=str(REPO_ROOT / "external/Fujitsu-Assessing-Compliance-in-Enterprise-Dataset/test.json"))
    p_conv.add_argument("--n", type=int, default=30)
    p_conv.add_argument("--cases-dir", default=None)
    p_conv.add_argument("--ruleset-dir", default=str(REPO_ROOT / "rulesets"))

    p_report = sub.add_parser("report", help="merge run results into one markdown report")
    p_report.add_argument("runs", nargs="+", help="results.json files or run dirs")
    p_report.add_argument("--out", default=None)

    p_leaderboard = sub.add_parser(
        "leaderboard", help="build a clickable local leaderboard from saved runs")
    p_leaderboard.add_argument("--runs-dir", default=str(REPO_ROOT / "var" / "runs"))
    p_leaderboard.add_argument("--out", default=str(REPO_ROOT / "var" / "leaderboard" / "index.html"))

    p_pages = sub.add_parser("pages", help="copy one campaign into a self-contained GitHub Pages leaderboard")
    p_pages.add_argument("--campaign-dir", required=True)
    p_pages.add_argument("--out", default=str(REPO_ROOT / "docs"))

    p_retry = sub.add_parser("retry-failures", help="rerun only API/JSON-error cases in one saved run")
    p_retry.add_argument("--run-dir", required=True, help="directory containing results.json and transcript.json")
    p_retry.add_argument("--offline", action="store_true")
    p_retry.add_argument("--max-tokens", type=int, default=8192)
    p_retry.add_argument("--gold", default=None, help="private gold YAML for an iri_review run")

    p_reprice = sub.add_parser(
        "reprice", help="recompute saved run costs from usage and the pinned model catalog")
    p_reprice.add_argument("--runs-dir", required=True)
    p_reprice.add_argument("--model", action="append", default=None,
                           help="limit to one or more model keys (repeatable)")

    p_rescore = sub.add_parser(
        "rescore", help="recompute saved rule-extraction scores from transcripts")
    p_rescore.add_argument("--runs-dir", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "run":
        from .run import resolve_fx_snapshot, run_benchmark
        fx_snapshot = (resolve_fx_snapshot(args.usd_rub, args.fx_date)
                       if args.usd_rub is not None or args.fx_date else None)
        res = run_benchmark(
            args.bench, args.model, Path(args.cases),
            ruleset_dir=Path(args.ruleset_dir), ruleset_id=args.ruleset,
            limit=args.limit, offline=args.offline,
            out_dir=Path(args.out) if args.out else None,
            max_tokens=args.max_tokens, effort=args.effort, fx_snapshot=fx_snapshot,
            gold_path=Path(args.gold) if args.gold else None,
            locale=args.locale, dataset_version=args.dataset_version,
            allow_repeat=args.allow_repeat,
            repeat_label=args.repeat_label,
        )
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
        print("results:", res["out_dir"])
        return 0

    if args.cmd == "campaign":
        from .run import run_campaign
        results = run_campaign(
            args.models, args.suites, offline=args.offline,
            out_dir=Path(args.out) if args.out else None,
            limit=args.limit, max_tokens=args.max_tokens,
            usd_rub=args.usd_rub, fx_date=args.fx_date,
        )
        for result in results:
            print(json.dumps({
                "model": result["model"],
                "benchmark": result["benchmark"],
                "dataset_version": result["dataset_version"],
                "cost_rub": result["summary"]["total_cost_rub"],
                "wall_time_s": result["wall_time_s"],
                "results": result["out_dir"],
            }, ensure_ascii=False))
        return 0

    if args.cmd == "pages":
        from .leaderboard import publish_pages
        result = publish_pages(Path(args.campaign_dir), Path(args.out))
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.cmd == "retry-failures":
        from .run import retry_failed_run
        result = retry_failed_run(
            Path(args.run_dir), offline=args.offline, max_tokens=args.max_tokens,
            gold_path=Path(args.gold) if args.gold else None,
        )
        print(json.dumps({
            "run": result["out_dir"],
            "retried": result.get("retry_history", [])[-1].get("case_ids", []) if result.get("retry_history") else [],
            "errors_remaining": result["summary"]["n_errors"],
            "wall_time_s": result["wall_time_s"],
        }, ensure_ascii=False))
        return 0

    if args.cmd == "reprice":
        from .run import reprice_saved_results
        result = reprice_saved_results(
            Path(args.runs_dir), models=set(args.model) if args.model else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "rescore":
        from .run import rescore_saved_results
        result = rescore_saved_results(Path(args.runs_dir))
        print(json.dumps(result, ensure_ascii=False, indent=2))
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
            currency = getattr(m, "price_currency", "USD")
            price = (f"{currency} {m.price_in}/{m.price_out} per 1M"
                     if m.price_in is not None else "no price")
            efforts = "/".join(m.effort_levels) if m.effort_levels else "-"
            print(f"{m.key:<26} {m.alias:<28} {m.provider:<10} {price:<24} "
                  f"effort[{efforts}] default={m.effort_default or '-'}"
                  + ("" if m.api_key else "  [NO KEY]"))
        return 0

    if args.cmd == "convert":
        from .converters import convert_ace
        cases_dir = Path(args.cases_dir) if args.cases_dir else REPO_ROOT / "cases" / f"{args.source}-test"
        written = convert_ace(Path(args.input), args.n, cases_dir, Path(args.ruleset_dir))
        n_pos = sum(1 for _, d in written if d == "accept")
        print(f"converted {len(written)} cases -> {cases_dir} "
              f"({n_pos} compliant / {len(written) - n_pos} non-compliant)")
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

    if args.cmd == "leaderboard":
        from .leaderboard import write_leaderboard
        result = write_leaderboard(Path(args.runs_dir), Path(args.out))
        print(f"leaderboard: {result['runs']} runs -> {result['out']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
