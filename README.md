# docbench — Document Conformance Benchmark

> Measure whether an LLM can replace the first line of formal document
> verification: input is a document packet plus a versioned, canonical ruleset;
> output is findings with mandatory evidence and a final disposition — scored
> against a deterministic oracle.

The pain: institutions (grant foundations, tax/reporting intake, compliance
desks) burn headcount on rule-by-rule document checks before any domain expert
even looks. Generic DocVQA numbers say nothing about that job. docbench turns
it into software-testable claims: case-level exact pass, finding precision /
recall, **false-accept and false-reject rates**, grounding quality, and cost
per case — metrics that translate directly into headcount and economics.

## What it does

- **Bench #1 `conformance`** — packet + canonical ruleset → findings / evidence /
  disposition; a deterministic rule engine (the oracle) regenerates gold from
  the mutated packet, so injected defects and expectations can never drift.
- **Bench #2 `rule_extraction`** — an institution policy document → a
  machine-checkable ruleset (field/op/value triples + severity).
- **Sidecar `errorgen`** — deterministic controlled corruption of valid packets
  (missing documents, contradicting sums, over-limit budgets, late dates,
  dropped signatures…). Gold is always recomputed by the oracle.
- **Sidecar `datasets`** — manifest-driven fetch of external benchmarks
  (ExtractBench, VAREX, ACE, CompliBench, TaxCalcBench, CiteVQA, OfficeQA),
  plus a working ACE→conformance converter.
- **Containerised verification** — everything except the LLM provider is pinned
  in a Docker image; offline mode scores deterministically with `--network none`.
- **Run metadata** — every run records provider, model alias, reasoning-effort
  label, the exact extra body params sent, and the served-model id echoed back
  (providers do not expose quantization; docbench records that honestly).

## Install

```bash
git clone https://github.com/megamen32/docbench && cd docbench
uv venv .venv && uv pip install -p .venv/bin/python -e . pytest
.venv/bin/python -m pytest -q          # 28 offline tests, no API keys needed
```

## Start in minutes

1. Generate corrupted cases and verify them against the oracle (no LLM, no keys):
   ```bash
   .venv/bin/docbench errorgen --plan cases/seed-grant/errorgen.yaml \
       --cases-dir cases/seed-grant --out cases/seed-grant
   ```
2. Add a provider key (OpenAI-compatible; MiniMax and Z.ai are pre-wired) in
   `~/.config/docbench/env` (chmod 600), see [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
3. Run the benchmark and get the full metrics report:
   ```bash
   .venv/bin/docbench run --bench conformance --model minimax-m2.7 --cases cases/seed-grant
   ```
4. Reproduce any run offline for free from the response cache:
   ```bash
   .venv/bin/docbench run --bench conformance --model minimax-m2.7 --offline --cases cases/seed-grant
   ```

## Headline results (2026-08-16)

Seed grants packet (10 cases) and real enterprise contracts (ACE, 30 scenarios):

| model | seed finding P/R | rule-extraction F1 | real-contracts false accept | cost/case |
|---|---|---|---|---|
| **GLM-4.7-Flash** | 1.000 / 1.000 | **0.689** | **12%** | free tier |
| MiniMax-M2.7 | 0.925 / 1.000 | 0.515 | 20% | ~$0.003 |
| MiniMax-M3 | 1.000 / 0.950 | 0.606 | 27% | ~$0.010 |

Full tables, the YAGNI ladder and the honest negative findings (seed results
do not transfer 1:1 to real contracts; a 5-scenario hard core fails every
model): **[RESULTS.md](RESULTS.md)** · leaderboard: [results/leaderboard.md](results/leaderboard.md).

## Learn more

- [Results and decisions](RESULTS.md) — comparative leaderboard, real-data run, model decisions
- [Configuration](docs/CONFIGURATION.md) — providers, keys, effort levels, pricing honesty
- [Containers](docs/CONTAINERS.md) — pinned offline/online verification modes
- [Datasets and licenses](docs/DATASETS.md) — registry, ACE CC BY 4.0 notice, gated repos
- [Full sanitized session transcript](TRANSCRIPT.md) — every model call, tool input/output, and decision of the build session
