# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| omniroute-routerai-gpt-5.4-mini | conformance | 30 | 0.7333 | — | — | — | 0.2000 | 0.0667 | — | — | 1.4166 | 30.5 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## omniroute-routerai-gpt-5.4-mini · conformance · 2026-08-20T12:22:51.293970+00:00

### Reasoning

- reason=capability present; DocBench requests thinking:false by default

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 49952 | 79205 | 129157 | 0 | 0 | 67422 | 42.499175 |

- ❌ `ace_0000` — disp accept vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ✅ `ace_0002` — disp reject vs needs_correction
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp needs_correction vs needs_correction
- ✅ `ace_0005` — disp accept vs accept
- ✅ `ace_0006` — disp reject vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ✅ `ace_0008` — disp needs_correction vs needs_correction
- ✅ `ace_0009` — disp accept vs accept
- ❌ `ace_0010` — disp accept vs needs_correction
- ✅ `ace_0011` — disp accept vs accept
- ✅ `ace_0012` — disp needs_correction vs needs_correction
- ❌ `ace_0013` — disp reject vs accept
- ❌ `ace_0014` — disp accept vs needs_correction
- ✅ `ace_0015` — disp accept vs accept
- ✅ `ace_0016` — disp reject vs needs_correction
- ✅ `ace_0017` — disp accept vs accept
- ✅ `ace_0018` — disp reject vs needs_correction
- ✅ `ace_0019` — disp accept vs accept
- ❌ `ace_0020` — disp accept vs needs_correction
- ✅ `ace_0021` — disp accept vs accept
- ✅ `ace_0022` — disp needs_correction vs needs_correction
- ✅ `ace_0023` — disp accept vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ❌ `ace_0026` — disp accept vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp needs_correction vs needs_correction
- ✅ `ace_0029` — disp accept vs accept
