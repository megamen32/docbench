# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yandexgpt-pro-5.1 | conformance | 30 | 0.4333 | — | — | — | 0.0690 | 0.4828 | — | — | 1.1454 | 3.4290 |

## yandexgpt-pro-5.1 · conformance · 2026-08-18T15:32:12.656947+00:00

### Reasoning

- reason=no exposed reasoning control in the OpenAI-compatible route

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 48102 | 11378 | 59480 | 9936 | 0 | 0 | 33.216938 |

- ✅ `ace_0000` — disp reject vs needs_correction
- ❌ `ace_0001` — disp needs_correction vs accept
- ❌ `ace_0002` — disp None vs None, parse: no JSON object in reply
- ❌ `ace_0003` — disp needs_correction vs accept
- ✅ `ace_0004` — disp reject vs needs_correction
- ❌ `ace_0005` — disp needs_correction vs accept
- ✅ `ace_0006` — disp reject vs needs_correction
- ❌ `ace_0007` — disp needs_correction vs accept
- ✅ `ace_0008` — disp reject vs needs_correction
- ❌ `ace_0009` — disp reject vs accept
- ✅ `ace_0010` — disp needs_correction vs needs_correction
- ❌ `ace_0011` — disp reject vs accept
- ✅ `ace_0012` — disp reject vs needs_correction
- ❌ `ace_0013` — disp needs_correction vs accept
- ✅ `ace_0014` — disp reject vs needs_correction
- ❌ `ace_0015` — disp reject vs accept
- ✅ `ace_0016` — disp reject vs needs_correction
- ❌ `ace_0017` — disp needs_correction vs accept
- ✅ `ace_0018` — disp reject vs needs_correction
- ❌ `ace_0019` — disp needs_correction vs accept
- ❌ `ace_0020` — disp accept vs needs_correction
- ❌ `ace_0021` — disp needs_correction vs accept
- ✅ `ace_0022` — disp reject vs needs_correction
- ❌ `ace_0023` — disp reject vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ✅ `ace_0026` — disp reject vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp reject vs needs_correction
- ❌ `ace_0029` — disp needs_correction vs accept
