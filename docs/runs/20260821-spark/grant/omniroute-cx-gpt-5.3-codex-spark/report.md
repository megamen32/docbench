# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| omniroute-cx-gpt-5.3-codex-spark | conformance | 20 | 0.9000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.9818 | 0.8250 | — | 4.1740 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## omniroute-cx-gpt-5.3-codex-spark · conformance · 2026-08-21T13:51:33.736662+00:00

### Reasoning

- reason=capability present; DocBench requests thinking:false by default

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 30912 | 76744 | 107656 | 22016 | 0 | 51014 | — |

- ✅ `grant_00001__corr_equipment_heavy` _(set_field: set budget.row.equipment.share_pct = 55.5)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_equipment_heavy` _(set_field: set budget.row.equipment.share_pct = 55.5)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_late_submission` _(shift_date: shifted application_form.submission_date: 2026-09-12 -> 2026-10-27)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_late_submission` _(shift_date: сдвиг application_form.submission_date: 2026-09-12 -> 2026-10-27)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_missing_budget` _(remove_document: removed required document 'budget' (Itemised budget))_ — disp reject vs reject
- ✅ `grant_00001__corr_missing_budget` _(remove_document: удалён обязательный документ 'budget' (Детализированная смета))_ — disp reject vs reject
- ✅ `grant_00001__corr_missing_registration` _(remove_document: removed required document 'registration_cert' (Registry extract))_ — disp reject vs reject
- ✅ `grant_00001__corr_missing_registration` _(remove_document: удалён обязательный документ 'registration_cert' (Выписка из реестра))_ — disp reject vs reject
- ✅ `grant_00001__corr_over_budget` _(scale_number: scaled ['budget.row.equipment.amount_eur', 'budget.row.other.amount_eur', 'budget.row.outreach.amount_eur', 'budget.row.personnel.amount_eur', 'budget.totals.total'] by 1.6)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_over_budget` _(scale_number: scaled ['budget.row.equipment.amount_eur', 'budget.row.other.amount_eur', 'budget.row.outreach.amount_eur', 'budget.row.personnel.amount_eur', 'budget.totals.total'] by 1.6)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_sum_mismatch` _(set_field: set application_form.requested_total_eur = 89200)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_sum_mismatch` _(set_field: set application_form.requested_total_eur = 89200)_ — disp needs_correction vs needs_correction
- ❌ `grant_00001__corr_unregistered` _(set_field: set application_form.months_registered = 3)_ — disp reject vs reject
- ❌ `grant_00001__corr_unregistered` _(set_field: set application_form.months_registered = 3)_ — disp reject vs reject
- ✅ `grant_00001__corr_unsigned` _(drop_signature: signature dropped (application_form.signature_present=false))_ — disp reject vs reject
- ✅ `grant_00001__corr_unsigned` _(drop_signature: подпись удалена (application_form.signature_present=false))_ — disp reject vs reject
- ✅ `grant_00001__corr_wrong_period` _(set_field: set finance_statement.period = 'FY2024')_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_wrong_period` _(set_field: set finance_statement.period = 'FY2024')_ — disp needs_correction vs needs_correction
- ✅ `grant_00001` — disp accept vs accept
- ✅ `grant_00001` — disp accept vs accept
