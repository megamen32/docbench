# DocBench — Russian document benchmark

> A small, auditable benchmark for comparing models on Russian document
verification and policy-rule extraction — with answers, tokens, latency and
cost recorded per run.

DocBench answers a practical question: can a model reliably perform the first
pass over a document packet or turn a written policy into explicit rules?
It is an evaluation tool, not legal advice or an automatic decision-maker.

## Run one comparable campaign

After configuring provider keys as described in
[Configuration](docs/CONFIGURATION.md), run every standard suite for selected
models in one command:

```bash
docbench campaign --models minimax-m2.5 yandexgpt-pro-5.1
```

The standard campaign currently contains 52 cases: 10 grant-conformance cases,
12 Russian policy-rule cases, and 30 ACE contract-conformance cases. To run a
single suite, use `--suite grant`, `--suite policy` or `--suite ace`.

Costs are presented in rubles. By default a campaign obtains the USD/RUB rate
from the Bank of Russia once and writes its date into the result. For a fully
specified replay, supply it yourself:

```bash
docbench campaign --models minimax-m2.5 --usd-rub 79.12 --fx-date 2026-08-18
```

Open the local, clickable results after a campaign:

```text
var/leaderboard/index.html
```

Click a model row to see that run's metrics and links to `results.json`,
`report.md` and, when retained, `transcript.json`.

## What the numbers mean

| Field | Meaning |
|---|---|
| Pass rate | Fraction of cases with a completely correct final result. For policy extraction it requires the complete gold ruleset and correct severity. |
| F1 | Partial overlap with gold rules/findings; useful when exact pass is too strict. |
| Errors | Transport/API failures or replies that could not be parsed as the required JSON. |
| API latency | Sum and per-case request latency; it is not campaign wall-clock time. |
| Cost | Provider-estimated or provider-reported token cost in rubles; USD prices are converted at the recorded CBR rate. |

Therefore **`pass rate = 0` and `errors = 0` is possible**: the model answered
valid JSON for every case, but none exactly matched the gold result. This is a
score, not an infrastructure failure.

Each new result records the selected provider/model, served-model id, reasoning
mode, input/output/cached/reasoning tokens, request latency and cost. Price
metadata states whether the value is an estimate. A model or provider that does
not publish a price is shown as unknown — never as free.

## Evidence boundary

For new runs, `transcript.json` contains the prompts, visible final model
answers, retries, usage and served model so a score can be inspected. It does
not retain private chain-of-thought or raw provider payloads. Older runs that
predate transcripts are visibly marked `legacy / no` and must not be presented
as equally auditable.

## Included suites

| Suite | Cases | Purpose | Dataset version |
|---|---:|---|---|
| Grant conformance | 10 | Verify a grant packet against fixed rules | `seed-grant-2026.1` |
| Policy rule extraction | 12 | Extract machine-checkable rules from self-authored Russian policies | [`ru-policy-seed-v1.0`](cases/seed-policy/DATASET.md) |
| ACE conformance | 30 | Check enterprise-contract scenarios through the conformance path | `ace-test-v1` |

The policy suite is a compact, diverse Russian v1 seed for repeatable model
comparison, not a representative corpus of Russian law. Do not rank models on
one suite alone; compare complete 52-case campaigns.

## More documentation

- [Configuration and providers](docs/CONFIGURATION.md)
- [Datasets and licences](docs/DATASETS.md)
- [Container/offline operation](docs/CONTAINERS.md)
