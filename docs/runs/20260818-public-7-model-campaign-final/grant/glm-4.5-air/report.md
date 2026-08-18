# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glm-4.5-air | conformance | 10 | 0.0000 | — | — | — | — | — | — | — | — | — |

## glm-4.5-air · conformance · 2026-08-18T14:24:42.664889+00:00

### Reasoning

- reason=not declared

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 0 | — |

- ❌ `grant_00001__corr_equipment_heavy` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_late_submission` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_missing_budget` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_missing_registration` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_over_budget` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_sum_mismatch` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_unregistered` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_unsigned` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001__corr_wrong_period` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
- ❌ `grant_00001` — disp None vs None, err: HTTP 401: {"error":{"code":"401","message":"token expired or incorrect"}}
