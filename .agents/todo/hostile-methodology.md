# Hostile methodology review — Russian supplementary benchmark

Verdict: **RETHINK**. The artifacts support a small, reproducible single-provider
supplementary campaign, not a defensible general leaderboard or an international/
Russian-model comparison. Do not make the latter claims until the verified defects
below are fixed and rerun.

## Verified defects

1. **P0 — the displayed aggregate ranks incompatible metrics and contains a known
   scoring artifact.**
   - Evidence: [docs/russian/index.html:10-12](../../docs/russian/index.html) calls
     57.8%, 55.6%, and 54.4% the mean pass rate of three equally weighted suites.
     For the policy suite it displays `0.0%` full match while also displaying F1
     81.3–95.1%. The underlying report explains every policy case as `disp None vs
     None` ([.../policy/.../report.md:21-32](../../docs/russian/runs/russian-20260823/policy/omniroute-cx-gpt-5.6-luna-low/report.md)); results nevertheless report
     finding F1 `0.9508` ([.../policy/.../results.json:103-116](../../docs/russian/runs/russian-20260823/policy/omniroute-cx-gpt-5.6-luna-low/results.json)).
   - Attack: the headline order is driven one-third by a field that does not apply
     to this task type, so it measures schema mismatch rather than rule extraction.
     It reverses the policy-suite F1 order (low > medium > high) in the displayed
     aggregate (medium > low > high).
   - Minimum fix/proof: remove `case_pass_rate` from cross-task aggregation or
     define and validate a task-appropriate normalized metric before the run; show
     the formula and recompute all rows from frozen artifacts.

2. **P0 — no uncertainty estimate supports rank claims.**
   - Evidence: the public table makes 2.2-point rank distinctions from one 52-case
     run per setting ([docs/russian/index.html:10-12](../../docs/russian/index.html)).
     Each result records one start/finish interval and no seed, sample count, or
     repeat statistic ([.../grant/.../results.json:2-16](../../docs/russian/runs/russian-20260823/grant/omniroute-cx-gpt-5.6-luna-low/results.json)); it uses a remote
     OpenAI-compatible route ([...:8-11](../../docs/russian/runs/russian-20260823/grant/omniroute-cx-gpt-5.6-luna-low/results.json)).
   - Attack: with provider/model sampling and no replicate campaign or CI, neither
     the ordering nor a small difference can be distinguished from run variance.
   - Minimum fix/proof: publish per-case paired outputs for >=3 independently
     timestamped repeats (or a justified deterministic setting), bootstrap CIs for
     each reported difference, and mark ties where intervals overlap.

3. **P1 — “3 models” is false as a model-family comparison.**
   - Evidence: the page says “Моделей 3” and lists only
     `omniroute-cx-gpt-5.6-luna-{low,medium,high}` ([docs/russian/index.html:9-11]).
     Result metadata identifies the same provider (`omniroute`) and served family
     `gpt-5.6-luna-low` for the low setting ([.../grant/.../results.json:8-24](../../docs/russian/runs/russian-20260823/grant/omniroute-cx-gpt-5.6-luna-low/results.json)).
   - Attack: this is an effort-setting ablation of one routed model family, not
     evidence that any model/provider/national group beats another. It cannot bear
     claims responding to the attached text’s price/competitiveness comparisons.
   - Minimum fix/proof: label these as three configurations of one model; for a
     leaderboard include predeclared independent model identities and disclose all
     routing/fallback/served-model records.

4. **P1 — construct validity is overstated: 40/52 cases are translations and the
   contract task is a binary disposition exercise with the rule embedded in input.**
   - Evidence: dataset README calls 10 grant and 30 ACE cases “translated”
     ([datasets/russian/README.md:3-15](../../datasets/russian/README.md)); in ACE
     the agreement text includes the governing condition immediately before the
     scenario ([datasets/russian/ace/cases/ace_0003_ru.yaml:8-31]) and the label
     scope is only `disposition` ([...:51-54](../../datasets/russian/ace/cases/ace_0003_ru.yaml)).
   - Attack: results do not establish broad Russian-document competence, OCR,
     evidence grounding, or realistic legal/document review; they largely test
     translated, self-contained prompt compliance and binary labels.
   - Minimum fix/proof: rename the claim to this exact construct, publish a
     representative native held-out document set with blinded expert labels and
     separate disposition, finding, and evidence-grounding scores.

5. **P1 — price numbers are estimates, yet the public table presents them as
   costs without an estimate qualifier.**
   - Evidence: UI labels columns “Стоимость, ₽” and “₽ / кейс”
     ([docs/russian/index.html:10-11]); the artifact marks `cost_is_estimate: true`
     and cites a pinned “supplement freeze” ([.../grant/.../results.json:22-24,
     114-117](../../docs/russian/runs/russian-20260823/grant/omniroute-cx-gpt-5.6-luna-low/results.json)).
   - Attack: readers can treat estimated router pricing as provider invoice cost,
     enabling the exact misleading price comparison criticized in the attached
     text.
   - Minimum fix/proof: visibly label every displayed number “estimate”, link the
     immutable rate card/FX assumptions, and separately report billable invoice or
     router usage if available.

## Unverified questions (do not allege without the requested proof)

1. **P1 — gold-label independence.**  Every translated ACE file has empty
   `expected_findings` and only a disposition label (e.g.
   [datasets/russian/ace/cases/ace_0003_ru.yaml:51-54](../../datasets/russian/ace/cases/ace_0003_ru.yaml)).
   Request: provenance, translator protocol, annotator count/blinding, adjudication,
   and agreement statistics. This is not proof that labels are wrong.

2. **P1 — Russian translation quality / source leakage.** The README admits
   translations but gives no translation-validation evidence
   ([datasets/russian/README.md:7-15](../../datasets/russian/README.md)).
   Request: source identifiers, licence proof, version mapping, independent
   bilingual semantic-equivalence audit, and contamination/leakage analysis.

3. **P2 — run reproducibility across time.** Artifacts pin code and input hashes
   ([.../policy/.../results.json:36-100](../../docs/russian/runs/russian-20260823/policy/omniroute-cx-gpt-5.6-luna-low/results.json)), which is useful, but do not prove
   the routed service will reproduce its outputs. Request replay results after a
   fixed interval, complete request parameters (including temperature/seed), and
   routing/fallback logs.
