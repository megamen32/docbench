# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| omniroute-cx-gpt-5.6-luna-low | conformance | 30 | 0.6667 | — | — | — | 0.1667 | 0.1667 | — | — | 0.0563 | 9.4340 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## omniroute-cx-gpt-5.6-luna-low · conformance · 2026-08-23T17:53:24.900735+00:00

### Reasoning

- reason=capability present; DocBench requests thinking:false by default

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 65853 | 15130 | 80983 | 1792 | 0 | 4313 | 1.690024 |

- ❌ `ace_0000` — disp accept vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ❌ `ace_0002` — disp accept vs needs_correction
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp needs_correction vs needs_correction
- ✅ `ace_0005` — disp accept vs accept
- ✅ `ace_0006` — disp reject vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ✅ `ace_0008` — disp needs_correction vs needs_correction
- ✅ `ace_0009` — disp accept vs accept
- ❌ `ace_0010` — disp accept vs needs_correction
- ❌ `ace_0011` — disp needs_correction vs accept
- ✅ `ace_0012` — disp needs_correction vs needs_correction
- ❌ `ace_0013` — disp needs_correction vs accept
- ❌ `ace_0014` — disp accept vs needs_correction
- ✅ `ace_0015` — disp accept vs accept
- ✅ `ace_0016` — disp needs_correction vs needs_correction
- ✅ `ace_0017` — disp accept vs accept
- ✅ `ace_0018` — disp needs_correction vs needs_correction
- ✅ `ace_0019` — disp accept vs accept
- ✅ `ace_0020` — disp needs_correction vs needs_correction
- ✅ `ace_0021` — disp accept vs accept
- ✅ `ace_0022` — disp reject vs needs_correction
- ❌ `ace_0023` — disp needs_correction vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ✅ `ace_0026` — disp needs_correction vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp needs_correction vs needs_correction
- ❌ `ace_0029` — disp needs_correction vs accept
