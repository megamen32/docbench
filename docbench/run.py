"""Run orchestration: cases -> model -> predictions -> strict metrics -> report."""
from __future__ import annotations

import json
import hashlib
import os
import statistics
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from xml.etree import ElementTree

from .benchmarks import BENCHMARKS
from .benchmarks.base import load_cases, load_ruleset, ruleset_index
from .config import REPO_ROOT, resolve_model
from .metrics import RULES_SCORE_VERSION
from .models.gigachat import GigaChatRunner
from .models.openai_compat import OpenAICompatRunner
from .schemas import Prediction

VAR_DIR = REPO_ROOT / "var"
CACHE_DIR = VAR_DIR / "cache"
RUNS_DIR = VAR_DIR / "runs"


def _canonical_sha256(value: Any) -> str:
    """Hash JSON data with a stable representation suitable for run manifests."""
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _path_label(path: Path) -> str:
    """Keep manifests portable when a caller supplied an absolute input path."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _file_manifest(paths: list[Path]) -> dict[str, Any]:
    """Return a deterministic content manifest for the inputs used by a run."""
    files = [
        {"path": _path_label(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(set(paths), key=_path_label)
    ]
    return {"sha256": _canonical_sha256(files), "files": files}


def _code_revision() -> dict[str, str | None]:
    """Identify the checked-out implementation without making git a runtime dependency."""
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        revision = None
    return {"git_revision": revision}


def _response_failure_kind(text: str | None) -> str | None:
    """Classify an explicit provider refusal without changing benchmark scoring."""
    normalized = " ".join((text or "").lower().split())
    if "я не могу обсуждать эту тему" in normalized:
        return "refusal"
    return None

# The small, supported campaign profile.  It keeps the currently useful
# document suites together without introducing a second manifest format.
CAMPAIGN_SUITES: dict[str, dict[str, Any]] = {
    "grant": {
        "benchmark": "conformance",
        "cases_path": REPO_ROOT / "cases" / "seed-grant",
        "dataset_version": "seed-grant-2026.1",
    },
    "policy": {
        "benchmark": "rule_extraction",
        "cases_path": REPO_ROOT / "cases" / "seed-policy",
        "dataset_version": "ru-policy-seed-v1.0",
    },
    "ace": {
        "benchmark": "conformance",
        "cases_path": REPO_ROOT / "cases" / "ace-test",
        "dataset_version": "ace-test-v1",
    },
}

CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


def _median(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 4) if xs else None


def _iso_cbr_date(value: str) -> str:
    """CBR returns DD.MM.YYYY in the daily XML document."""
    return datetime.strptime(value, "%d.%m.%Y").date().isoformat()


def fetch_cbr_usd_rub() -> dict[str, Any]:
    """Fetch the official USD rate once, for a campaign-level frozen ledger."""
    try:
        with urlopen(CBR_DAILY_URL, timeout=15) as response:  # nosec B310: fixed official URL
            root = ElementTree.fromstring(response.read())
    except Exception as exc:
        raise RuntimeError(
            "could not fetch the CBR USD/RUB rate; pass --usd-rub and --fx-date for an offline campaign"
        ) from exc
    usd = next((v for v in root.findall("Valute") if v.findtext("CharCode") == "USD"), None)
    if usd is None:
        raise RuntimeError("CBR daily XML did not contain USD")
    nominal = float((usd.findtext("Nominal") or "1").replace(",", "."))
    value = float((usd.findtext("Value") or "").replace(",", "."))
    if nominal <= 0 or value <= 0:
        raise RuntimeError("CBR daily XML contained an invalid USD rate")
    return {
        "usd_rub": round(value / nominal, 6),
        "date": _iso_cbr_date(root.attrib["Date"]),
        "source": "CBR",
        "source_url": CBR_DAILY_URL,
    }


def resolve_fx_snapshot(usd_rub: float | None = None, fx_date: str | None = None) -> dict[str, Any]:
    """Use an explicit pinned rate, or obtain one official CBR snapshot."""
    if usd_rub is not None:
        if not fx_date:
            raise ValueError("--fx-date is required together with --usd-rub")
        if usd_rub <= 0:
            raise ValueError("--usd-rub must be positive")
        return {"usd_rub": usd_rub, "date": fx_date, "source": "explicit"}
    if fx_date:
        raise ValueError("--usd-rub is required together with --fx-date")
    return fetch_cbr_usd_rub()


def run_benchmark(
    bench_key: str,
    model_key: str,
    cases_path: Path,
    *,
    ruleset_dir: Path | None = None,
    ruleset_id: str | None = None,
    limit: int | None = None,
    offline: bool = False,
    out_dir: Path | None = None,
    max_tokens: int = 8192,
    effort: str | None = None,
    dataset_version: str | None = None,
    fx_snapshot: dict[str, Any] | None = None,
    gold_path: Path | None = None,
    case_ids: set[str] | None = None,
    use_cache: bool | None = None,
    locale: str = "en",
) -> dict[str, Any]:
    if bench_key not in BENCHMARKS:
        raise KeyError(f"unknown benchmark {bench_key!r}; known: {sorted(BENCHMARKS)}")
    if locale not in {"en", "ru"}:
        raise ValueError(f"unsupported prompt locale {locale!r}")
    # An online benchmark is an observation of a provider, not a cache replay.
    # Offline reproduction deliberately remains cache-backed.
    use_cache = offline if use_cache is None else use_cache
    spec = resolve_model(model_key, allow_missing_key=offline)
    extra_body = spec.effort_extra(effort)
    effort_label = effort or spec.effort_default or "provider-default"
    runner_cls = (GigaChatRunner if getattr(spec, "auth_method", "bearer") == "gigachat_oauth"
                  else OpenAICompatRunner)
    runner = runner_cls(spec, cache_dir=CACHE_DIR if use_cache else None, offline=offline)

    started_at = datetime.now(timezone.utc)
    run_started_monotonic = time.monotonic()

    pairs = load_cases(Path(cases_path))
    if case_ids is not None:
        available = {case.id for _, case in pairs}
        missing = sorted(case_ids - available)
        if missing:
            raise KeyError(f"unknown case ids for {cases_path}: {missing}")
        pairs = [(path, case) for path, case in pairs if case.id in case_ids]
    if limit:
        pairs = pairs[:limit]
    has_private = any(case.private for _, case in pairs)
    ruleset_paths: list[Path] = []
    rulesets: dict[str, Any] = {}
    if bench_key == "conformance":
        active_ruleset_dir = Path(ruleset_dir) if ruleset_dir else REPO_ROOT / "rulesets"
        rulesets = ruleset_index(active_ruleset_dir)
        ruleset_paths_by_id = {
            load_ruleset(path).id: path for path in sorted(active_ruleset_dir.glob("*.yaml"))
        }
        for _, case in pairs:
            rid = ruleset_id or case.ruleset
            if rid and rid in ruleset_paths_by_id:
                ruleset_paths.append(ruleset_paths_by_id[rid])
    reproducibility = {
        "schema_version": 1,
        "code": _code_revision(),
        "inputs": {
            "cases": _file_manifest([path for path, _ in pairs]),
            "rulesets": _file_manifest(ruleset_paths),
            "gold": _file_manifest([gold_path]) if gold_path else None,
        },
    }

    per_case: list[dict[str, Any]] = []
    transcript_cases: list[dict[str, Any]] = []
    bench = None
    for path, case in pairs:
        if bench_key == "conformance":
            rid = ruleset_id or case.ruleset
            if not rid:
                raise ValueError(f"case {case.id}: no ruleset id")
            if rid not in rulesets:
                raise KeyError(f"case {case.id}: ruleset {rid!r} not found in rulesets/")
            bench = BENCHMARKS[bench_key](rulesets[rid], locale=locale)
        elif bench_key == "iri_review":
            bench = BENCHMARKS[bench_key](gold_path=gold_path)
        else:
            bench = BENCHMARKS[bench_key](locale=locale)
        gold = bench.gold_for(case)
        msgs = bench.messages(case, gold)
        t0 = time.monotonic()
        cost_usd = 0.0
        cost_rub_direct = 0.0
        cost_est = False
        comp = None
        payload, parse_err = None, None
        attempts: list[dict[str, Any]] = []
        for attempt in range(2):
            try:
                comp = runner.complete(msgs, max_tokens=max_tokens, extra_body=extra_body)
            except Exception as e:  # network failure must not kill the run
                attempts.append({
                    "attempt": attempt + 1,
                    "messages": msgs,
                    "messages_sha256": _canonical_sha256(msgs),
                    "error": str(e)[:300],
                })
                per_case.append({"case_id": case.id, "ok": False, "error": str(e)[:300],
                                 "cost_rub": None, "cost_usd": None, "latency_s": None})
                comp = None
                break
            attempts.append({
                "attempt": attempt + 1,
                "messages": msgs,
                "messages_sha256": _canonical_sha256(msgs),
                # Completion.text is the final answer after chain-of-thought stripping.
                "response_text": comp.text,
                "usage": comp.usage,
                "served_model": comp.model,
                "latency_s": comp.latency_s,
                "cache_hit": comp.cache_hit,
                "response_receipt_sha256": _canonical_sha256({
                    "text": comp.text, "usage": comp.usage, "served_model": comp.model,
                }),
            })
            cost_usd += getattr(comp, "cost_usd", None) or 0.0
            cost_rub_direct += getattr(comp, "cost_rub", None) or 0.0
            cost_est = cost_est or comp.cost_is_estimate
            payload, parse_err = bench.parse(comp.text, case)
            if payload is not None:
                break
            if attempt == 0:
                # reasoning models sometimes close <think> and stop: nudge once
                msgs = msgs + [{"role": "user",
                                "content": "Your previous reply contained no JSON. "
                                           "Output ONLY the JSON object now, starting with '{' "
                                           "with no preamble and no reasoning."}]
        if comp is None:
            transcript_cases.append({"case_id": case.id, "attempts": attempts})
            continue
        wall = round(time.monotonic() - t0, 3)
        if payload is None:
            scores = {"ok": False, "parse_error": parse_err}
            failure_kind = _response_failure_kind(comp.text)
            if failure_kind:
                scores["response_kind"] = failure_kind
            pred_dump: dict[str, Any] = {"raw_head": (comp.text or "")[:400]}
        else:
            scores = bench.score(payload, gold, case)
            if parse_err:
                scores["parse_warning"] = parse_err
            pred_dump = _payload_dump(payload)
        row = {
            "case_id": case.id,
            "source": str(path),
            "generated_by": case.generated_by,
            **scores,
            "cost_rub": _cost_to_rub(cost_usd, cost_rub_direct, fx_snapshot),
            "cost_usd": round(cost_usd, 9) if cost_usd else None,
            "cost_is_estimate": cost_est,
            "latency_s": comp.latency_s or wall,
            "cache_hit": comp.cache_hit,
            # A malformed first answer can be retried once; ledger totals must
            # include both billable attempts, not only the final parseable one.
            "usage": {**_attempt_usage(attempts), "served_model": comp.model},
        }
        per_case.append(row)
        transcript_cases.append({"case_id": case.id, "attempts": attempts})

    finished_at = datetime.now(timezone.utc)
    summary = _aggregate(per_case)
    result = {
        "ts": finished_at.isoformat(),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "wall_time_s": round(time.monotonic() - run_started_monotonic, 3),
        "benchmark": bench_key,
        "locale": locale,
        "model": spec.key,
        "model_alias": spec.alias,
        "provider": spec.provider,
        "provider_label": spec.provider_label,
        "effort": effort_label,
        "request_extra": extra_body,
        "cache_mode": "read_write" if use_cache else "bypass",
        "local_cache_hits": sum(1 for row in per_case if row.get("cache_hit")),
        "provider_endpoint": runner.base_url,
        "quantization": spec.quantization,
        "quantization_note": ("providers do not expose served quantization via API; "
                              "pin provider+model+date and see served_models"),
        "served_models": sorted({c.get("usage", {}).get("served_model") for c in per_case
                                 if c.get("usage", {}).get("served_model")}),
        "price_source": spec.price_source,
        "price_currency": getattr(spec, "price_currency", "USD"),
        "pricing_snapshot": getattr(spec, "pricing_snapshot", None),
        "fx_snapshot": fx_snapshot,
        "reasoning": getattr(spec, "reasoning", None),
        "reasoning_note": getattr(spec, "reasoning_note", None),
        "artifacts": {"transcript": "transcript.json.gitcrypt" if has_private else "transcript.json"},
        "cases_path": str(cases_path),
        "gold_scope": "external_private" if bench_key == "iri_review" else None,
        "private": has_private,
        "dataset_version": dataset_version or f"{Path(cases_path).name}-v1",
        "scoring_version": RULES_SCORE_VERSION,
        "reproducibility": reproducibility,
        "n_cases": len(per_case),
        "summary": summary,
        "cases": per_case,
    }
    out = out_dir or (RUNS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{bench_key}-{spec.key}")
    out.mkdir(parents=True, exist_ok=True)
    result["out_dir"] = str(out)
    (out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    transcript = {
        "schema_version": 1,
        "run": {
            "benchmark": bench_key,
            "locale": locale,
            "model": spec.key,
            "model_alias": spec.alias,
            "provider": spec.provider,
            "result": "results.json",
            "reproducibility": reproducibility,
        },
        # Prompts and final answers are auditable. Private chain-of-thought and
        # unfiltered raw provider payloads are deliberately not retained.
        "cases": transcript_cases,
    }
    _write_transcript(out, transcript, private=has_private)
    (out / "report.md").write_text(render_markdown_report([result]), encoding="utf-8")
    return result


def retry_failed_run(
    run_dir: Path,
    *,
    offline: bool = False,
    max_tokens: int = 8192,
    gold_path: Path | None = None,
) -> dict[str, Any]:
    """Retry failed rows only, then atomically merge them into an existing run."""
    run_dir = Path(run_dir)
    result_path = run_dir / "results.json"
    transcript_path = run_dir / "transcript.json"
    original = json.loads(result_path.read_text(encoding="utf-8"))
    if original.get("private") or original.get("artifacts", {}).get("transcript") != "transcript.json":
        raise ValueError("retry-failures supports runs with a plaintext transcript.json only")
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    failed_ids = {row["case_id"] for row in original.get("cases", [])
                  if row.get("error") or row.get("parse_error")}
    if not failed_ids:
        return original

    effort = original.get("effort")
    if effort == "provider-default":
        effort = None
    with tempfile.TemporaryDirectory(prefix="docbench-retry-") as temp:
        retry = run_benchmark(
            original["benchmark"], original["model"], Path(original["cases_path"]),
            offline=offline, out_dir=Path(temp), max_tokens=max_tokens,
            effort=effort, dataset_version=original.get("dataset_version"),
            fx_snapshot=original.get("fx_snapshot"), gold_path=gold_path,
            case_ids=failed_ids, use_cache=False, locale=original.get("locale", "en"),
        )
        retry_transcript = json.loads((Path(temp) / "transcript.json").read_text(encoding="utf-8"))

    retry_rows = {row["case_id"]: row for row in retry["cases"]}
    merged_cases = [retry_rows.get(row["case_id"], row) for row in original["cases"]]
    retry_index = len(original.get("retry_history", [])) + 1
    retry_attempts = {case["case_id"]: case.get("attempts", []) for case in retry_transcript["cases"]}
    for case in transcript.get("cases", []):
        if case["case_id"] in retry_attempts:
            case.setdefault("attempts", []).extend(
                [{**attempt, "retry": retry_index} for attempt in retry_attempts[case["case_id"]]]
            )

    finished_at = retry["finished_at"]
    merged = dict(original)
    merged.update({
        "ts": finished_at,
        "finished_at": finished_at,
        "wall_time_s": round(float(original.get("wall_time_s") or 0) + float(retry["wall_time_s"]), 3),
        "served_models": sorted({row.get("usage", {}).get("served_model") for row in merged_cases
                                 if row.get("usage", {}).get("served_model")}),
        "n_cases": len(merged_cases),
        "summary": _aggregate(merged_cases),
        "cases": merged_cases,
        "out_dir": str(run_dir),
    })
    history = list(original.get("retry_history", []))
    history.append({
        "at": finished_at,
        "retry_index": retry_index,
        "case_ids": sorted(failed_ids),
        "wall_time_s": retry["wall_time_s"],
        "cache_mode": retry["cache_mode"],
        "summary": retry["summary"],
    })
    merged["retry_history"] = history

    result_tmp = result_path.with_suffix(".json.tmp")
    transcript_tmp = transcript_path.with_suffix(".json.tmp")
    result_tmp.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    transcript_tmp.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(result_tmp, result_path)
    os.replace(transcript_tmp, transcript_path)
    (run_dir / "report.md").write_text(render_markdown_report([merged]), encoding="utf-8")
    return merged


def reprice_saved_results(runs_dir: Path, *, models: set[str] | None = None) -> dict[str, Any]:
    """Fill missing per-case costs from the pinned catalog without rerunning APIs.

    This is intentionally offline: usage already persisted in a run is the
    billing input, while the model catalog supplies the frozen token rates.
    Scores, answers, timestamps and transcripts are left untouched.
    """
    changed: list[str] = []
    skipped: list[str] = []
    # os.walk(..., followlinks=True) is intentional: campaign indexes use
    # symlinked model directories to keep one canonical result per run.
    result_paths = [Path(root) / name
                    for root, _dirs, files in os.walk(runs_dir, followlinks=True)
                    for name in files if name == "results.json"]
    for result_path in sorted(result_paths):
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            spec = resolve_model(str(result.get("model")), allow_missing_key=True)
        except (OSError, json.JSONDecodeError, KeyError, RuntimeError):
            skipped.append(str(result_path))
            continue
        if models and spec.key not in models:
            continue
        if spec.price_in is None or spec.price_out is None:
            skipped.append(str(result_path))
            continue
        touched = False
        for case in result.get("cases", []):
            usage = case.get("usage") or {}
            if not usage:
                continue
            cache_read = int(usage.get("cache_read_input_tokens") or 0)
            cache_write = int(usage.get("cache_write_input_tokens") or 0)
            input_total = int(usage.get("input_tokens") or 0)
            uncached = usage.get("uncached_input_tokens")
            if uncached is None:
                uncached = max(input_total - cache_read - cache_write, 0)
            cost = (int(uncached) * spec.price_in
                    + cache_read * (spec.price_cache_read if spec.price_cache_read is not None else spec.price_in)
                    + cache_write * (spec.price_cache_write if spec.price_cache_write is not None else spec.price_in)
                    + int(usage.get("output_tokens") or 0) * spec.price_out) / 1e6
            case["cost_rub"] = round(cost, 6) if spec.price_currency == "RUB" else case.get("cost_rub")
            if spec.price_currency == "USD":
                case["cost_usd"] = round(cost, 9)
            case["cost_is_estimate"] = True
            touched = True
        if not touched:
            continue
        result["summary"] = _aggregate(result.get("cases", []))
        result["price_source"] = spec.price_source
        result["price_currency"] = spec.price_currency
        result["pricing_snapshot"] = spec.pricing_snapshot
        result["pricing_recalculated"] = True
        result["pricing_recalculation_note"] = (
            "cost recomputed offline from persisted usage and the pinned catalog; no API rerun"
        )
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        report_path = result_path.with_name("report.md")
        if report_path.is_file():
            report_path.write_text(render_markdown_report([result]), encoding="utf-8")
        changed.append(str(result_path))
    return {"changed": changed, "skipped": skipped}


def rescore_saved_results(runs_dir: Path) -> dict[str, Any]:
    """Recompute rule-extraction scores from saved plaintext transcripts.

    This is offline and never calls a provider.  It updates only the derived
    score fields and report, preserving every response, prompt, timestamp,
    usage record, and cost ledger.
    """
    changed: list[str] = []
    skipped: list[str] = []
    score_fields = {
        "precision", "recall", "f1", "tp", "gold_rules", "pred_rules",
        "severity_accuracy", "unmatched_gold", "unmatched_pred", "ok",
        "pred_disposition", "gold_disposition", "false_accept", "false_reject",
        "finding_precision", "finding_recall", "finding_f1", "critical_recall",
        "grounding_precision", "grounding_recall", "extraction_f1", "parse_error",
        "parse_warning",
    }
    for result_path in sorted(Path(runs_dir).glob("**/results.json")):
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            skipped.append(str(result_path))
            continue
        if result.get("benchmark") != "rule_extraction":
            continue
        transcript_path = result_path.with_name("transcript.json")
        if not transcript_path.is_file():
            skipped.append(str(result_path))
            continue
        cases_path = Path(str(result.get("cases_path", "")))
        if not cases_path.is_absolute():
            cases_path = REPO_ROOT / cases_path
        try:
            cases = {case.id: case for _, case in load_cases(cases_path)}
            transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            skipped.append(str(result_path))
            continue
        transcript_by_id = {str(item.get("case_id")): item for item in transcript.get("cases", [])}
        bench = BENCHMARKS["rule_extraction"]()
        rescored: list[dict[str, Any]] = []
        for old in result.get("cases", []):
            row = dict(old)
            case = cases.get(str(old.get("case_id")))
            tcase = transcript_by_id.get(str(old.get("case_id")))
            attempts = (tcase or {}).get("attempts", [])
            response = next((attempt.get("response_text") for attempt in reversed(attempts)
                             if attempt.get("response_text") is not None), None)
            if case is None or response is None:
                rescored.append(row)
                continue
            payload, parse_err = bench.parse(str(response), case)
            row = {key: value for key, value in row.items() if key not in score_fields}
            if payload is None:
                row.update({"ok": False, "parse_error": parse_err or "no JSON object in reply"})
            else:
                scores = bench.score(payload, bench.gold_for(case), case)
                if parse_err:
                    scores["parse_warning"] = parse_err
                row.update(scores)
            rescored.append(row)
        if rescored == result.get("cases", []) and result.get("scoring_version") == RULES_SCORE_VERSION:
            continue
        result["cases"] = rescored
        result["summary"] = _aggregate(rescored)
        result["scoring_version"] = RULES_SCORE_VERSION
        tmp = result_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, result_path)
        report_path = result_path.with_name("report.md")
        report_path.write_text(render_markdown_report([result]), encoding="utf-8")
        changed.append(str(result_path))
    return {"changed": changed, "skipped": skipped, "score_version": RULES_SCORE_VERSION}


def _write_transcript(out_dir: Path, transcript: dict[str, Any], *, private: bool) -> Path:
    """Write a run transcript, encrypting it when any case is marked private.

    ``git-crypt clean`` is used directly so no plaintext temporary file is
    created.  A private run fails closed if git-crypt is unavailable, locked,
    or returns data without its ciphertext marker.
    """
    raw = json.dumps(transcript, ensure_ascii=False, indent=2).encode("utf-8")
    if not private:
        path = out_dir / "transcript.json"
        path.write_bytes(raw)
        return path

    plain_path = out_dir / "transcript.json"
    if plain_path.exists():
        raise RuntimeError(
            "refusing private transcript because plaintext transcript.json already exists"
        )
    try:
        proc = subprocess.run(
            ["git-crypt", "clean"],
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPO_ROOT,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("private transcript requires git-crypt to be installed") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()[-300:]
        raise RuntimeError(f"could not encrypt private transcript with git-crypt: {detail}") from exc
    if not proc.stdout.startswith(b"\x00GITCRYPT\x00"):
        raise RuntimeError("git-crypt did not return a ciphertext transcript")
    path = out_dir / "transcript.json.gitcrypt"
    path.write_bytes(proc.stdout)
    return path


def _cost_to_rub(cost_usd: float, cost_rub_direct: float, fx_snapshot: dict[str, Any] | None) -> float | None:
    if cost_rub_direct:
        return round(cost_rub_direct, 6)
    if cost_usd and fx_snapshot:
        return round(cost_usd * float(fx_snapshot["usd_rub"]), 6)
    return None


def _attempt_usage(attempts: list[dict[str, Any]]) -> dict[str, int]:
    fields = ("input_tokens", "output_tokens", "total_tokens", "cache_read_input_tokens",
              "cache_write_input_tokens", "cache_input_tokens", "uncached_input_tokens",
              "reasoning_tokens")
    return {
        field: sum(int((attempt.get("usage") or {}).get(field) or 0) for attempt in attempts)
        for field in fields
    }


def run_campaign(
    models: list[str],
    suites: list[str] | None = None,
    *,
    offline: bool = False,
    out_dir: Path | None = None,
    max_tokens: int = 8192,
    limit: int | None = None,
    usd_rub: float | None = None,
    fx_date: str | None = None,
) -> list[dict[str, Any]]:
    """Run selected models over the standard suites under one frozen FX snapshot."""
    selected = suites or list(CAMPAIGN_SUITES)
    unknown = sorted(set(selected) - set(CAMPAIGN_SUITES))
    if unknown:
        raise KeyError(f"unknown campaign suites: {unknown}; known: {sorted(CAMPAIGN_SUITES)}")
    if offline and usd_rub is None:
        raise ValueError("offline campaign requires --usd-rub and --fx-date; it cannot fetch CBR")
    fx_snapshot = resolve_fx_snapshot(usd_rub, fx_date)
    campaign_dir = out_dir or (RUNS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-campaign")
    results: list[dict[str, Any]] = []
    for suite in selected:
        profile = CAMPAIGN_SUITES[suite]
        for model in models:
            result = run_benchmark(
                profile["benchmark"], model, profile["cases_path"],
                limit=limit, offline=offline, max_tokens=max_tokens,
                out_dir=campaign_dir / suite / model.replace("/", "_"),
                dataset_version=profile["dataset_version"], fx_snapshot=fx_snapshot,
            )
            results.append(result)
    return results


def _aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(cases)
    errors = [c for c in cases if c.get("error") or c.get("parse_error")]
    scored = [c for c in cases if "finding_precision" in c]

    def mean(k: str) -> float | None:
        vals = [c[k] for c in scored if c.get(k) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    costs = [c["cost_rub"] for c in cases if c.get("cost_rub") is not None]
    token_fields = ["input_tokens", "output_tokens", "total_tokens", "cache_read_input_tokens",
                    "cache_write_input_tokens", "cache_input_tokens", "reasoning_tokens"]
    token_totals = {field: sum((c.get("usage", {}).get(field) or 0) for c in cases)
                    for field in token_fields}
    lats = [c["latency_s"] for c in cases if c.get("latency_s") is not None]
    return {
        "n_cases": n,
        "n_scored": len(scored),
        "n_errors": len(errors),
        "case_pass_rate": round(sum(1 for c in cases if c.get("ok")) / n, 4) if n else None,
        "finding_precision": mean("finding_precision"),
        "finding_recall": mean("finding_recall"),
        "finding_f1": mean("finding_f1"),
        "critical_recall": mean("critical_recall"),
        "grounding_precision": mean("grounding_precision"),
        "grounding_recall": mean("grounding_recall"),
        "extraction_f1": mean("extraction_f1"),
        "false_accept_rate": round(sum(1 for c in scored if c.get("false_accept")) / len(scored), 4) if scored else None,
        "false_reject_rate": round(sum(1 for c in scored if c.get("false_reject")) / len(scored), 4) if scored else None,
        "cost_per_case_rub": round(sum(costs) / len(costs), 6) if costs else None,
        "cost_is_estimate": any(c.get("cost_is_estimate") for c in cases),
        "latency_p50_s": _median(lats),
        "total_cost_rub": round(sum(costs), 6) if costs else None,
        "tokens": token_totals,
    }


def _payload_dump(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    if "findings" in out:
        out["findings"] = [f.model_dump(exclude_none=True) if hasattr(f, "model_dump") else f
                           for f in out["findings"]]
    if "rules" in out:
        out["rules"] = [r.model_dump(exclude_none=True) if hasattr(r, "model_dump") else r
                        for r in out["rules"]]
    return out


def render_markdown_report(results: list[dict[str, Any]]) -> str:
    lines = ["# docbench report", ""]
    cols = ["model", "benchmark", "n_cases", "case_pass_rate", "finding_precision",
            "finding_recall", "critical_recall", "false_accept_rate", "false_reject_rate",
            "extraction_f1", "grounding_recall", "cost_per_case_rub", "latency_p50_s"]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * len(cols))
    for r in results:
        s = r.get("summary", {})
        row = []
        for c in cols:
            v = r.get(c, s.get(c))
            if isinstance(v, float):
                v = f"{v:.4f}" if v < 10 else f"{v:.1f}"
            row.append(str(v) if v is not None else "—")
        lines.append("| " + " | ".join(row) + " |")
    est = any(r.get("summary", {}).get("cost_is_estimate") for r in results)
    if est:
        lines.append("")
        lines.append("_Note: the pinned supplement has no separate cache rate; "
                     "cache tokens are counted separately and charged once at the pinned input rate._")
    lines.append("")
    for r in results:
        lines.append(f"## {r.get('model')} · {r.get('benchmark')} · {r.get('ts', '')}")
        lines.append("")
        lines.append("### Reasoning")
        lines.append("")
        lines.append(f"- reason={r.get('reasoning_note') or ('matters' if r.get('reasoning') else 'not declared')}")
        lines.append("")
        tokens = r.get("summary", {}).get("tokens", {})
        lines.append("### Tokens and cost")
        lines.append("")
        lines.append("| input | output | total | cache read | cache write | reasoning | cost RUB |")
        lines.append("|---:|---:|---:|---:|---:|---:|---:|")
        lines.append("| {input_tokens} | {output_tokens} | {total_tokens} | {cache_read_input_tokens} | {cache_write_input_tokens} | {reasoning_tokens} | {cost} |".format(
            input_tokens=tokens.get("input_tokens", 0), output_tokens=tokens.get("output_tokens", 0),
            total_tokens=tokens.get("total_tokens", 0), cache_read_input_tokens=tokens.get("cache_read_input_tokens", 0),
            cache_write_input_tokens=tokens.get("cache_write_input_tokens", 0), reasoning_tokens=tokens.get("reasoning_tokens", 0),
            cost=r.get("summary", {}).get("total_cost_rub") or "—"))
        lines.append("")
        for c in r.get("cases", []):
            flag = "✅" if c.get("ok") else "❌"
            gen = f" _({', '.join(c['generated_by'])})_" if c.get("generated_by") else ""
            lines.append(f"- {flag} `{c['case_id']}`{gen}"
                         f" — disp {c.get('pred_disposition')} vs {c.get('gold_disposition')}"
                         + (f", err: {c['error']}" if c.get("error") else "")
                         + (f", parse: {c['parse_error']}" if c.get("parse_error") else "")
                         + (f", response: {c['response_kind']}" if c.get("response_kind") else ""))
        lines.append("")
    return "\n".join(lines)
