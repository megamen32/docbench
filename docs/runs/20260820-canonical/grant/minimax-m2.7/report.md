# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_rub | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| minimax-m2.7 | conformance | 10 | 0.9000 | 0.9250 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.9727 | 0.8750 | 0.2324 | 18.8 |

_Note: the pinned supplement has no separate cache rate; cache tokens are counted separately and charged once at the pinned input rate._

## minimax-m2.7 · conformance · 2026-08-20T10:50:21.428536+00:00

### Reasoning

- reason=not declared

### Tokens and cost

| input | output | total | cache read | cache write | reasoning | cost RUB |
|---:|---:|---:|---:|---:|---:|---:|
| 14868 | 18715 | 33583 | 0 | 0 | 0 | 2.323532 |

- ✅ `grant_00001__corr_equipment_heavy` _(set_field: set budget.row.equipment.share_pct = 55.5)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_late_submission` _(shift_date: shifted application_form.submission_date: 2026-09-12 -> 2026-10-27)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_missing_budget` _(remove_document: removed required document 'budget' (Itemised budget))_ — disp reject vs reject
- ❌ `grant_00001__corr_missing_registration` _(remove_document: removed required document 'registration_cert' (Registry extract))_ — disp reject vs reject
- ✅ `grant_00001__corr_over_budget` _(scale_number: scaled ['budget.row.equipment.amount_eur', 'budget.row.other.amount_eur', 'budget.row.outreach.amount_eur', 'budget.row.personnel.amount_eur', 'budget.totals.total'] by 1.6)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_sum_mismatch` _(set_field: set application_form.requested_total_eur = 89200)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_unregistered` _(set_field: set application_form.months_registered = 3)_ — disp reject vs reject
- ✅ `grant_00001__corr_unsigned` _(drop_signature: signature dropped (application_form.signature_present=false))_ — disp reject vs reject
- ✅ `grant_00001__corr_wrong_period` _(set_field: set finance_statement.period = 'FY2024')_ — disp needs_correction vs needs_correction
- ✅ `grant_00001` — disp accept vs accept
