# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glm-4.7-flash | rule_extraction | 12 | 0.0000 | 0.7828 | 0.7828 | — | 0.0000 | 0.0000 | — | — | 0.1218 | 12.7 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## glm-4.7-flash · rule_extraction · 2026-08-18T15:22:06.562358+00:00

### Reasoning

- reason=not declared

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 4228 | 24759 | 28987 | 1962 | 0 | 21638 | 1.09594 |

- ❌ `policy_cultural_grant` — disp None vs None
- ❌ `policy_education_license` — disp None vs None
- ❌ `policy_energy_efficiency` — disp None vs None
- ❌ `policy_foundation_v2` — disp None vs None, err: glm-4.7-flash: request failed after 6 retries
- ❌ `policy_grant_2026` — disp None vs None
- ❌ `policy_housing_repair` — disp None vs None
- ❌ `policy_medical_procurement` — disp None vs None
- ❌ `policy_microloan` — disp None vs None
- ❌ `policy_municipal_subsidy` — disp None vs None, err: glm-4.7-flash: request failed after 6 retries
- ❌ `policy_procurement_supplier` — disp None vs None, err: glm-4.7-flash: request failed after 6 retries
- ❌ `policy_research_competition` — disp None vs None
- ❌ `policy_social_contract` — disp None vs None
