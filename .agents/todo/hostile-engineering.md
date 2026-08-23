# Hostile engineering audit — 2026-08-23

Scope: current `main` at `b2150429cd2ed4f3f581a56bfa4022195661d54a`, against the
attached critique's reproducibility/transparency standard. Read-only audit; no
provider calls, Docker build, or public-site browser acceptance were performed.

## Verified defects

### P0 — Published "fresh" benchmark rows can be entirely local-cache replays

- **Evidence:** `docs/runs/20260820-canonical/grant/gigachat-3-ultra/results.json:5,13,37-54`
  reports `wall_time_s: 1.27`, `cache_mode: read_write`, and p50 12.105 s; all
  10 case rows have `cache_hit: true`. `policy/glm-4.7-flash/results.json` is
  likewise 12/12 local-cache hits and 0.064 s wall time. The current runner
  enables local cache for ordinary campaigns (`docbench/run.py:157,169,314`),
  and the public table advertises a comparison of quality and speed without a
  local-cache-hit marker (`docbench/leaderboard.py:374-404,484-489`).
- **Attack:** a "campaign" can present old answers from an unknown earlier
  request as a dated fresh provider comparison. Its displayed wall time is then
  cache-read time, not API performance. The cache record has no acquisition
  time, base URL, provider request ID, code/input digest, or immutable response
  receipt (`docbench/models/openai_compat.py:126-163`), so a hostile reader
  cannot establish what was actually called.
- **Minimum fix/proof:** default published online campaigns to `use_cache=False`
  (or fail Pages publication on any local hit); retain cache only for explicitly
  labelled offline replay. Publish per-case `local_cache_hit`, acquisition
  timestamp, effective base URL (redacted as needed), request-id/response hash,
  and a campaign manifest. Re-run one complete 52-case, cache-cold campaign per
  compared model and publish the receipts.

### P0 — Public release lacks the provenance fields implemented by current code

- **Evidence:** the same checked-in public result has no `reproducibility`,
  `scoring_version`, `locale`, or `retry_history` fields (JSON key checks are
  false); see `docs/runs/20260820-canonical/grant/gigachat-3-ultra/results.json:1-60`.
  Current code only now emits source revision/input manifests at
  `docbench/run.py:196-204,330-332`. The release workflow runs pytest only and
  does not regenerate/verify Pages artifacts or an image digest
  (`.github/workflows/release-validation.yml:1-18`).
- **Attack:** public transcripts show prompts and answers but cannot prove which
  code, scoring version, case bytes, ruleset bytes, or retry history produced
  their scores. A source/test fix after the run does not repair this release.
- **Minimum fix/proof:** regenerate every public campaign (or mark legacy,
  non-comparable) with current manifest schema; require Pages validation to
  reject results missing code SHA, scoring version, input hashes and complete
  retry history. Publish the commit SHA and a content manifest for each page
  campaign.

### P1 — ACE "Полное совпадение" is only a binary disposition agreement

- **Evidence:** for `gold.scope == "disposition"`, ACE scoring sets `ok` solely
  from `accept` versus non-`accept` (`docbench/benchmarks/conformance.py:143-158`).
  Yet the public table labels `case_pass_rate` as "Полное совпадение"
  (`docbench/leaderboard.py:374-404`), and published ACE rows report values such
  as 66.67% (`docs/runs/20260820-canonical/ace/omniroute-cx-gpt-5.6-luna-low/results.json:40-53`).
- **Attack:** a response with a wrong/missing rule finding, fabricated evidence,
  or wrong severity still receives a complete-match pass whenever its final
  disposition has the right accept/non-accept polarity. This invalidates any
  public reading of ACE pass-rate as formal document verification accuracy.
- **Minimum fix/proof:** label this metric `binary disposition agreement` in
  all public UI/report fields, or obtain/publish case-level gold and score every
  finding/evidence. Re-render historical ACE tables after the label correction.

### P1 — Container claim "everything ... pinned" is false at the OS/image layer

- **Evidence:** Dockerfile uses mutable tags `ghcr.io/astral-sh/uv:0.10.8` and
  `python:3.10-slim` (`Dockerfile:5-6`), while `docs/CONTAINERS.md:3-5` says
  everything except the LLM provider is pinned. `uv.lock` locks Python package
  dependencies, not the two image manifests.
- **Attack:** rebuilding the documented command at a later date can silently
  change Python/OS/uv bytes despite an unchanged repository and lockfile.
- **Minimum fix/proof:** pin both `FROM` images by immutable sha256 digest,
  record the resulting image digest in each run manifest, and publish a clean
  `--network none` rebuild/replay receipt for that digest.

### P1 — No uncertainty estimate or independent fresh repetitions supports rank claims

- **Evidence:** `run_campaign` executes exactly one run per `(suite, model)`
  (`docbench/run.py:634-663`); there is no seed, replicate count, or confidence
  interval in the result schema. The attached text specifically challenges
  ranking claims smaller than evaluator/model variance.
- **Attack:** a one-shot, opaque-provider snapshot cannot distinguish a real
  model gap from sampling/provider-version/routing drift. The current
  `served_models` echo is useful but does not identify all provider changes.
- **Minimum fix/proof:** for any comparative/rank claim, run a predeclared
  cache-cold repeated protocol (at least three independent trials, fixed prompt
  and model settings), publish trial-level rows and uncertainty/paired-delta
  intervals. Otherwise label results as a dated single-run observation, not a
  ranking.

### P2 — Retry mutates one run into a mixed-time, mixed-provider measurement without UI warning

- **Evidence:** retry replaces failed rows in place and updates the top-level
  finish time/summary (`docbench/run.py:394-426`), while keeping successful rows
  from the original request. The retry itself bypasses cache (`:385-391`), but
  the top-level `cache_mode` is not changed; public cards/tables do not render
  `retry_history` (no references in `docbench/leaderboard.py`).
- **Attack:** a no-error/"готово" row may combine calls from different moments
  (and potentially different served variants) while looking like one coherent
  campaign. It can mask asymmetric outage/rate-limit treatment.
- **Minimum fix/proof:** make retry create an immutable attempt/run revision, or
  render a prominent `mixed retry` badge with case IDs, timestamps, served IDs,
  cache mode and original/error outcomes; exclude mixed rows from strict
  head-to-head rankings unless every model follows the same retry protocol.

### P2 — Claimed grounding can be credited without verifying the claimed locator or quote

- **Evidence:** `grounded_prf` accepts a true positive when any evidence field
  is present and the document id matches; it does not compare locator/quote to
  gold (`docbench/metrics.py:25-42`).
- **Attack:** a model can attach a wrong passage from the right document and
  receive grounding credit, overstating evidence-grounded verification.
- **Minimum fix/proof:** score locator/quote against a canonical span or
  normalized source text and report document-only versus span-grounded metrics
  separately; add adversarial tests with wrong quotes in the correct document.

## Unverified questions (do not treat as defects yet)

1. **Live Pages provenance:** no live browser/HTTP check was run. Confirm that
   `megamen32.github.io/docbench` serves commit `b2150429`, not merely the local
   `docs/` tree; save deployed commit/SHA and public fetch digest.
2. **Provider-routing identity:** result JSON records alias and sometimes served
   model, but does not persist effective base URL or provider request ID. Check
   whether OmniRoute can silently route one alias to multiple underlying models;
   if yes, add route/served-id receipts before cross-model claims.
3. **ACE conversion reproducibility:** NOTICE gives upstream repository and a
   converter command (`NOTICE:3-7`), but this audit did not fetch the upstream
   commit or recompute the 30 converted cases. Pin and publish upstream commit,
   conversion command/version, and case-hash manifest.
4. **Docker execution evidence:** Docker was not built or run in this audit.
   The Dockerfile may work with its current registry tags; the verified issue is
   non-immutability, not a demonstrated build failure.
