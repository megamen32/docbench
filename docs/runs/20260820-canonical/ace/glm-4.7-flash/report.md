# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glm-4.7-flash | conformance | 30 | 0.5667 | — | — | — | 0.1200 | 0.2000 | — | — | 0.2822 | 91.5 |

## glm-4.7-flash · conformance · 2026-08-20T11:07:46.513288+00:00

### Reasoning

- reason=not declared

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 69742 | 185710 | 255452 | 0 | 0 | 0 | 8.466518 |

- ❌ `ace_0000` — disp accept vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ❌ `ace_0002` — disp None vs None, parse: no JSON object in reply
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp needs_correction vs needs_correction
- ✅ `ace_0005` — disp accept vs accept
- ✅ `ace_0006` — disp reject vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ❌ `ace_0008` — disp None vs None, parse: no JSON object in reply
- ❌ `ace_0009` — disp reject vs accept
- ❌ `ace_0010` — disp None vs None, parse: no JSON object in reply
- ✅ `ace_0011` — disp accept vs accept
- ✅ `ace_0012` — disp reject vs needs_correction
- ❌ `ace_0013` — disp reject vs accept
- ❌ `ace_0014` — disp None vs None, parse: no JSON object in reply
- ✅ `ace_0015` — disp accept vs accept
- ❌ `ace_0016` — disp None vs None, parse: no JSON object in reply
- ✅ `ace_0017` — disp accept vs accept
- ✅ `ace_0018` — disp reject vs needs_correction
- ✅ `ace_0019` — disp accept vs accept
- ❌ `ace_0020` — disp accept vs needs_correction
- ✅ `ace_0021` — disp accept vs accept
- ✅ `ace_0022` — disp reject vs needs_correction
- ❌ `ace_0023` — disp needs_correction vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ✅ `ace_0026` — disp needs_correction vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp reject vs needs_correction
- ❌ `ace_0029` — disp needs_correction vs accept
