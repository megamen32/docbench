# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gigachat-3-ultra | conformance | 30 | 0.7333 | — | — | — | 0.1000 | 0.1667 | — | — | — | 5.3500 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## gigachat-3-ultra · conformance · 2026-08-20T11:07:57.546633+00:00

### Reasoning

- reason=no provider reasoning field requested

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 45847 | 14212 | 60059 | 0 | 0 | 0 | — |

- ✅ `ace_0000` — disp needs_correction vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ✅ `ace_0002` — disp reject vs needs_correction
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp reject vs needs_correction
- ✅ `ace_0005` — disp accept vs accept
- ✅ `ace_0006` — disp needs_correction vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ✅ `ace_0008` — disp reject vs needs_correction
- ❌ `ace_0009` — disp reject vs accept
- ✅ `ace_0010` — disp needs_correction vs needs_correction
- ✅ `ace_0011` — disp accept vs accept
- ✅ `ace_0012` — disp reject vs needs_correction
- ❌ `ace_0013` — disp needs_correction vs accept
- ✅ `ace_0014` — disp reject vs needs_correction
- ❌ `ace_0015` — disp needs_correction vs accept
- ✅ `ace_0016` — disp needs_correction vs needs_correction
- ✅ `ace_0017` — disp accept vs accept
- ✅ `ace_0018` — disp reject vs needs_correction
- ✅ `ace_0019` — disp accept vs accept
- ❌ `ace_0020` — disp accept vs needs_correction
- ✅ `ace_0021` — disp accept vs accept
- ❌ `ace_0022` — disp accept vs needs_correction
- ✅ `ace_0023` — disp accept vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ✅ `ace_0026` — disp reject vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp reject vs needs_correction
- ❌ `ace_0029` — disp reject vs accept
