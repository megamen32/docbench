# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yandex-alice-ai-llm | conformance | 30 | 0.8000 | — | — | — | 0.0345 | 0.1379 | — | — | 1.2229 | 5.6130 |

## yandex-alice-ai-llm · conformance · 2026-08-20T12:35:40.399731+00:00

### Reasoning

- reason=no exposed reasoning control in the OpenAI-compatible route

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 48131 | 22298 | 70429 | 11136 | 0 | 0 | 35.4634 |

- ✅ `ace_0000` — disp needs_correction vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ❌ `ace_0002` — disp None vs None, parse: no JSON object in reply, response: refusal
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp reject vs needs_correction
- ✅ `ace_0005` — disp accept vs accept
- ✅ `ace_0006` — disp needs_correction vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ✅ `ace_0008` — disp needs_correction vs needs_correction
- ✅ `ace_0009` — disp accept vs accept
- ✅ `ace_0010` — disp needs_correction vs needs_correction
- ✅ `ace_0011` — disp accept vs accept
- ✅ `ace_0012` — disp reject vs needs_correction
- ❌ `ace_0013` — disp needs_correction vs accept
- ✅ `ace_0014` — disp needs_correction vs needs_correction
- ✅ `ace_0015` — disp accept vs accept
- ✅ `ace_0016` — disp needs_correction vs needs_correction
- ✅ `ace_0017` — disp accept vs accept
- ✅ `ace_0018` — disp reject vs needs_correction
- ✅ `ace_0019` — disp accept vs accept
- ✅ `ace_0020` — disp needs_correction vs needs_correction
- ❌ `ace_0021` — disp needs_correction vs accept
- ✅ `ace_0022` — disp needs_correction vs needs_correction
- ✅ `ace_0023` — disp accept vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ✅ `ace_0026` — disp reject vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp reject vs needs_correction
- ❌ `ace_0029` — disp needs_correction vs accept
