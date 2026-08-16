# docbench — Document Conformance Benchmark

Может ли система заменить первую линию формальной проверки документов при
фиксированном наборе институциональных правил? Это не очередной DocVQA:
вход — пакет документов + канонический версионированный ruleset, выход —
findings с обязательным evidence/provenance и финальный disposition.

```
canonical rules (versioned) ──┐
                              ├──▶  MODEL  ──▶ extracted facts
PDF / XLSX / forms / images ──┘                verification findings (rule → status → evidence)
                                              final disposition (accept / needs_correction / reject)
```

## What's inside

| Component | What it does |
|---|---|
| **bench #1 `conformance`** | packet + ruleset → findings/evidence/disposition, scored against a deterministic oracle |
| **bench #2 `rule_extraction`** | institution policy document → machine-readable ruleset (field/op/value triples + severity) |
| **sidecar `datasets`** | manifest-driven fetch of external benchmark datasets (`datasets/registry.yaml`) |
| **sidecar `errorgen`** | deterministic controlled corruption of valid packets; gold always recomputed by the oracle |
| **oracle** | deterministic rule engine (flatten packet → evaluate every rule → gold findings + disposition) |

## Repo layout

```
docbench/            python package (schemas, oracle, metrics, runner, benchmarks, errorgen, CLI)
rulesets/            canonical versioned rulesets (seed-grant-2026.1)
cases/               benchmark cases: seed-grant (conformance), seed-policy (rule_extraction)
datasets/            registry.yaml + downloaded data (data/ is gitignored)
external/            cloned source benchmarks (gitignored, reproducible via scripts/fetch_external.sh)
tests/               offline unit tests (deterministic, no network)
var/                 runs, response cache (gitignored)
```

## Quickstart

```bash
uv venv .venv && uv pip install -p .venv/bin/python -e . pytest

# model catalog (key from ~/.config/docbench/env or env vars)
.venv/bin/docbench models

# generate corrupted cases from the valid packet (gold = oracle, no drift)
.venv/bin/docbench errorgen --plan cases/seed-grant/errorgen.yaml \
    --cases-dir cases/seed-grant --out cases/seed-grant/corrupted

# bench #1 on the cheap bootstrap model
.venv/bin/docbench run --bench conformance --model minimax-m2.7 \
    --cases cases/seed-grant --ruleset-dir rulesets

# bench #2
.venv/bin/docbench run --bench rule_extraction --model minimax-m2.7 \
    --cases cases/seed-policy

# offline rerun from response cache (free, deterministic)
.venv/bin/docbench run --bench conformance --model minimax-m2.7 --offline --cases cases/seed-grant

# datasets sidecar
.venv/bin/docbench datasets list
.venv/bin/docbench datasets fetch --all

# merge run results into one leaderboard
.venv/bin/docbench report var/runs/*/results.json --out var/leaderboard.md
```

## Metrics (strict, headcount-translatable)

- **case-level exact pass rate** — полное совпадение findings+disposition с оракулом
- **finding precision / recall / F1** — по violation-находкам (match по rule_id)
- **critical violation recall** — доля пойманных критических нарушений
- **false accept rate** — дефектный пакет принят автоматически (главный риск)
- **false reject rate** — корректный пакет не принят
- **extraction F1** — value F1 по canonical fields (null ≠ missing, выдуманные поля штрафуются)
- **grounding precision/recall** — TP засчитывается только с evidence в правильном документе
- **cost per case / latency p50** — экономика одной заявки

## Models & secrets

Провайдеры описаны в `docbench/models.yaml` (OpenAI-compatible endpoints).
Ключи читаются из окружения, затем из `~/.config/docbench/env` (chmod 600).
Ключи никогда не коммитятся и не передаются через argv.
Цены в каталоге помечены `price_source` — до сверки с реальными счетами
стоимость считается оценочной.

## External sources (fork candidates)

`scripts/fetch_external.sh` клонирует (depth 1):

- run-llama/ExtractBench — document+schema→JSON с grounding (главный кандидат форка)
- FujitsuResearch/…-Assessing-Compliance-in-Enterprise-Dataset (ACE) — scenario+clauses→compliant/non-compliant
- UCSB-NLP-Chang/CompliBench — guidelines+violations, шаблон генерации недочётов
- udibarzi/varex-bench — 1777 форм, schema-per-document (анти-memorization)
- opendatalab/CiteVQA — QA с page/bbox provenance
- applicaai/kleister-charity — реальные годовые отчёты фондов (git-annex)
- column-tax/tax-calc-bench — closed-scope 100% correctness precedent
- databricks/officeqa (+pro-v2) — grounded reasoning по финансовым документам

## Tests

```bash
.venv/bin/python -m pytest -q
```

Все тесты оффлайн и детерминированы; e2e-прогон модели кэшируется в `var/cache`,
повторные запуски бесплатны.
