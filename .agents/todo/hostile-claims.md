# Hostile claim audit — 2026-08-23

## Resolution status — 2026-08-23

- Resolved: Pages were regenerated from the canonical renderer; every local
  row now targets a generated `run.html` with sibling results/transcript files.
- Resolved in scope: the Russian page no longer claims a cross-suite winner or
  a statistical ranking from one run.
- Still outside DocBench proof: historical post pricing/rank claims, legal
  conclusions, and provider-invoice assertions require primary external sources.

Scope: 20 August DocBench price/quality posts in
`/home/roomhacker/.codex/attachments/41d4c2bb-93cc-46b9-9692-73840d962142/pasted-text.txt`,
the linked live page `https://megamen32.github.io/docbench/index.html`, and
current `main` (`b2150429`). This is an adversarial evidence audit, not a
finding that a historical price or external ranking is false.

## Verified defects / attackable overclaims

- **P0 — the linked public proof is broken.** Evidence: live root `index.html`
  (SHA-256 `5ea092...11ba`) renders a row href
  `runs/russian-20260823/grant/omniroute-cx-gpt-5.6-luna-medium/run.html`; a
  live GET to that URL returns **404**, while the existing artifact is under
  `/docbench/russian/runs/...` (200). The page says: “Кликните по строке,
  чтобы открыть полный транскрипт и детали прогона.” Attack: the claimed
  auditable transcript/details are unavailable from every current-root row;
  a reader cannot independently inspect the evidence. Minimum correction:
  publish the assets at the linked paths or generate root-relative links, then
  HTTP-verify every row and raw `results.json`/`transcript.json` link.

- **P1 — the post link no longer substantiates the advertised comparison.**
  Evidence: the 20 Aug post links `https://megamen32.github.io/docbench/` and
  names MiniMax M3, Kimi, GLM, Terra, Sol, GigaChat, Alice and Yandex; live
  root page dated `23.08.2026 21:14` contains exactly three
  `omniroute-cx-gpt-5.6-luna-{low,medium,high}` models. Attack: the live link
  supplies no visible historical campaign, rate card, or archive that proves
  the published 13-model pricing list or the promised “итоги реального
  тестирования”. Minimum correction: add a dated immutable campaign/archive
  URL to the post, with model/provider/route identifiers and the exact post
  table; otherwise state that the link is to a later, different snapshot.

- **P1 — two quoted 2M-input/1M-output figures conflict with the repository's
  only pinned rate source.** Evidence: post quote: “GPT 5.6 Terra ≈ 1 340 ₽”
  and “GPT 5.6 Sol ≈ 3 340 ₽”; `docbench/pricing_snapshot.json:1-18` declares
  `pricing_basis: routerai`, `usd_rub: 82.9977`, Terra $1.30/$7.80 per 1M and
  Sol $6.50/$39.00. Its own arithmetic gives **863.18 ₽** Terra and **4315.88
  ₽** Sol for 2M input + 1M output (MiniMax M3 does approximately match:
  153.21 ₽ vs post 150 ₽). Attack: without an archived historical rate card,
  the exact numbers look selectively or incorrectly calculated; current
  public evidence cannot reproduce them. Minimum correction: publish the
  dated source URL/snapshot, currency rate, input/output/cache/reasoning
  billing assumptions and formula for every price; explicitly label figures
  estimates where they are not invoices.

- **P1 — “дороже всех в несколько раз” / “не входит в топ-10” has no
  identified comparison universe.** Evidence: reply post says “посмотрим на
  бенчмарк гигачата от Сбера. Он даже не входит в топ-10”; current public
  DocBench is a 52-case, three-suite document test. `README.md:104-112` says
  its policy data are “self-authored” and “not a representative corpus”, and
  warns not to rank on one suite. Attack: neither “top-10” nor “all” names a
  benchmark version, metric, date, submitted models, price basis, or exact
  GigaChat SKU; a bounded document benchmark cannot establish a general model
  ranking. Minimum correction: cite the specific Sber leaderboard snapshot and
  say e.g. “rank X/Y by metric M on dataset/version/date”; keep DocBench claims
  scoped to its named suites.

- **P1 — quality rhetoric overreaches the experiment.** Evidence: post:
  “вы правда считаете что вы лучше GLM и GPT 5.6 TERRA...” and reply:
  “дорогие и бесполезные”; live page headline promises “Сравнение качества,
  скорости, стоимости и полноты ответов.” But current page has 52 constructed
  cases, three models, each `thinking:false`; `README.md:4-9,104-112` limits
  the product to first-pass document/policy work and says it is not an
  automatic decision-maker or representative corpus. No confidence intervals,
  repeated seeds, user-success outcome, or cross-task result is published.
  Attack: a vendor can accurately say the evidence shows only this prompt set
  under this route/configuration, not that its model is generally inferior or
  useless. Minimum correction: replace global verdicts with suite/config/date
  statements, report error handling and uncertainty/repeat policy, and separate
  opinion from measured fact.

- **P1 — route and model identity are materially under-disclosed for a
  direct-price/quality comparison.** Evidence: public run metadata calls the
  provider “OmniRoute (OpenAI-compatible)”, alias
  `cx/gpt-5.6-luna-medium`, served model `gpt-5.6-luna-medium`, and price
  source “supplement freeze 01f9c5c (openai/gpt-5.6-luna-pro base)” in
  `docs/russian/runs/.../run.html`; `docbench/pricing_snapshot.json:1-18`
  labels its basis `routerai`. Attack: a reader can mistake routed aliases and
  a supplement estimate for direct-provider model, SKU, availability, or
  invoice price. This especially weakens “купленный напрямую у провайдера” if
  applied to any routed row. Minimum correction: every public comparison row
  must show vendor, purchase route/reseller, request alias, served-model id,
  effort/temperature, rate source/version, and whether price is estimated or
  invoiced; do not use “directly bought” unless documented per row.

- **P2 — legal/reputation risk is unsupported by DocBench.** Evidence: the
  pasted posts assert, among other things, “абсолютно не конкурентоспособны”,
  “не пытаются”, “жируют на ... налоги”, and imply regulatory capture/causal
  motives. No DocBench artifact contains evidence about intent, procurement,
  tax funding, legal effect, market-wide competitiveness, or corporate conduct.
  Attack: measured price or a small benchmark score does not prove motive or
  misconduct; categorical accusations invite a defamation/reputation response.
  Minimum correction: remove/mark these as opinion, or attach primary legal,
  corporate and procurement sources and obtain a publication-specific legal
  review; do not present them as DocBench findings.

## Unverified questions (do not assert as defects yet)

- Were the 20 Aug figures based on a preserved historical provider price page,
  actual invoices, a reseller tariff, promotional tier, or a different
  input/output/cache/reasoning mix? The current snapshot may post-date/change
  the rates; retrieve the dated source before labelling the Terra/Sol figures
  false.
- Which exact model SKUs were meant by “Kimi K2.7 Code”, “GLM-5.2”, “Alice”,
  and “GigaChat Max”, and were all prices for the same API tier, region,
  currency conversion and billing mode? Current repository does not establish
  that mapping for the post.
- Which exact external “бенчмарк гигачата от Сбера” establishes the claimed
  rank, and what is the archived table/date? It is not identified in the post
  or DocBench.
- Does the “one day / half-million” headline mean a planned synthetic spend or
  a completed invoiced spend? No run manifest, invoice, token total, or
  campaign-budget calculation is linked publicly.
