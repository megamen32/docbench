# docbench — Document Conformance Benchmark

> **Measure whether an LLM can replace the first line of document verification.**
>
> Transform subjective human rule checks into software-testable claims:
> exact pass/fail, precision/recall, false-accept/reject rates, grounding quality, and per-case cost.

---

## 🚀 30-second overview

- **What it does**: Takes a document packet + versioned ruleset → AI findings with mandatory evidence and a final disposition, scored against a deterministic oracle.
- **The problem it solves**: Institutions burn headcount on rule-by-rule document checks before any expert looks. Generic DocVQA numbers say nothing about this job.
- **What you get**: Metrics that translate directly into headcount and economics—case-level exact pass, finding precision/recall, false-accept and false-reject rates, grounding quality, and cost per case.

### One-line install

```bash
pip install docbench
```

---

## 📋 Quick start

```bash
# 1. Verify corrupted cases offline (no API keys needed)
docbench errorgen --plan cases/seed-grant/errorgen.yaml \
    --cases-dir cases/seed-grant --out cases/seed-grant

# 2. Run conformance benchmark against an LLM
docbench run --bench conformance --model minimax-m2.7 --cases cases/seed-grant

# 3. Reproduce runs offline from cache (free)
docbench run --bench conformance --model minimax-m2.7 --offline --cases cases/seed-grant
```

---

## ✨ Key features

| Feature | What it gives you |
|---------|-------------------|
| **Bench #1: conformance** | Packet + ruleset → findings/evidence/disposition with deterministic oracle |
| **Bench #2: rule_extraction** | Policy document → machine-checkable ruleset (field/op/value triples + severity) |
| **Sidecar: errorgen** | Deterministic corruption of valid packets (missing docs, contradicting sums, over-limit budgets, late dates, dropped signatures…) with gold recomputed by the oracle |
| **Sidecar: datasets** | Manifest-driven fetch of external benchmarks (ExtractBench, VAREX, ACE, CompliBench, TaxCalcBench, CiteVQA, OfficeQA) + ACE→conformance converter |
| **Containerised verification** | Everything except LLM provider pinned in Docker; offline mode with `--network none` for deterministic scoring |
| **Run metadata** | Every run records provider, model alias, reasoning-effort label, extra body params, and the served-model id (providers don't expose quantization; docbench records that honestly) |

---

## 📊 Real-world results (2026-08-16)

Seed grants packet (10 cases) and real enterprise contracts (ACE, 30 scenarios):

| Model | Seed Finding P/R | Rule Extraction F1 | Real-Contracts False Accept | Cost/Case |
|-------|------------------|-------------------|----------------------------|-----------|
| **GLM-4.7-Flash** | 1.000 / 1.000 | **0.689** | **12%** | free tier |
| MiniMax-M2.7 | 0.925 / 1.000 | 0.515 | 20% | ~$0.003 |
| MiniMax-M3 | 1.000 / 0.950 | 0.606 | 27% | ~$0.010 |

Full tables, YAGNI ladder, and honest negative findings: **[RESULTS.md](RESULTS.md)** · **[results/leaderboard.md](results/leaderboard.md)**

---

## 📚 More documentation

- [Results and decisions](RESULTS.md) — comparative leaderboard, real-data run, model decisions
- [Configuration](docs/CONFIGURATION.md) — providers, keys, effort levels, pricing honesty
- [Containers](docs/CONTAINERS.md) — pinned offline/online verification modes
- [Datasets and licenses](docs/DATASETS.md) — registry, ACE CC BY 4.0 notice, gated repos
- [Full sanitized session transcript](TRANSCRIPT.md) — every model call, tool input/output, and decision of the build session

---

## 🏷️ Project tags

#LLM #Benchmark #DocumentVerification #Conformance #RuleExtraction #ACE #CompliBench #DocVQA
