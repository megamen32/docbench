# docbench report

| model | benchmark | n_cases | case_pass_rate | rule_exact_f1 | finding_precision | finding_recall | severity_accuracy | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| omniroute-cx-gpt-5.6-luna-high | rule_extraction | 12 | 0.0000 | 0.3840 | 0.8131 | 0.8131 | 0.5500 | — | 0.0000 | 0.0000 | — | — | 0.0511 | 10.1 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## omniroute-cx-gpt-5.6-luna-high · rule_extraction · 2026-08-23T17:50:07.082789+00:00

### Reasoning

- reason=capability present; DocBench requests thinking:false by default

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 6205 | 8429 | 14634 | 0 | 0 | 3892 | 0.612629 |

- ❌ `policy_cultural_grant` — disp None vs None
- ❌ `policy_education_license` — disp None vs None
- ❌ `policy_energy_efficiency` — disp None vs None
- ❌ `policy_foundation_v2` — disp None vs None
- ❌ `policy_grant_2026` — disp None vs None
- ❌ `policy_housing_repair` — disp None vs None
- ❌ `policy_medical_procurement` — disp None vs None
- ❌ `policy_microloan` — disp None vs None
- ❌ `policy_municipal_subsidy` — disp None vs None
- ❌ `policy_procurement_supplier` — disp None vs None
- ❌ `policy_research_competition` — disp None vs None
- ❌ `policy_social_contract` — disp None vs None
