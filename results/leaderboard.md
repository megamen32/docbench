# docbench report

| model | benchmark | n_cases | case_pass_rate | finding_precision | finding_recall | critical_recall | false_accept_rate | false_reject_rate | extraction_f1 | grounding_recall | cost_per_case_usd | latency_p50_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| minimax-m2.7 | conformance | 10 | 0.9000 | 0.9250 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.9727 | 0.8750 | 0.0027 | 18.8 |
| minimax-m2.7-highspeed | conformance | 10 | 0.5000 | 0.9167 | 0.9167 | 1.0000 | 0.0000 | 0.0000 | 0.9697 | 0.7778 | 0.0025 | 19.2 |
| minimax-m2.7-highspeed | rule_extraction | 2 | 0.0000 | 0.5606 | 0.5606 | — | 0.0000 | 0.0000 | — | — | 0.0024 | 26.1 |
| minimax-m2.7 | rule_extraction | 2 | 0.0000 | 0.5152 | 0.5152 | — | 0.0000 | 0.0000 | — | — | 0.0017 | 15.0 |
| minimax-m3 | conformance | 10 | 0.9000 | 1.0000 | 0.9500 | 1.0000 | 0.0000 | 0.0000 | 0.9818 | 0.8250 | 0.0103 | 11.4 |
| minimax-m3 | rule_extraction | 2 | 0.0000 | 0.6061 | 0.6061 | — | 0.0000 | 0.0000 | — | — | 0.0101 | 23.5 |
| minimax-m2.7 | conformance | 30 | 0.5667 | — | — | — | 0.2000 | 0.2333 | — | — | 0.0025 | 20.7 |
| minimax-m3 | conformance | 30 | 0.5333 | — | — | — | 0.2667 | 0.2000 | — | — | 0.0104 | 17.2 |
| glm-4.7-flash | conformance | 10 | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.9818 | 0.8000 | — | 64.8 |
| glm-4.7-flash | rule_extraction | 2 | 0.0000 | 0.6894 | 0.6894 | — | 0.0000 | 0.0000 | — | — | — | 74.1 |
| glm-4.7-flash | conformance | 30 | 0.5667 | — | — | — | 0.1200 | 0.2000 | — | — | — | 91.5 |

_Note: cost computed from catalog prices flagged as estimates; override in docbench/models.yaml with invoiced prices._

## minimax-m2.7 · conformance · 2026-08-16T14:16:09.367691+00:00

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

## minimax-m2.7-highspeed · conformance · 2026-08-16T14:19:46.223301+00:00

- ✅ `grant_00001__corr_equipment_heavy` _(set_field: set budget.row.equipment.share_pct = 55.5)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_late_submission` _(shift_date: shifted application_form.submission_date: 2026-09-12 -> 2026-10-27)_ — disp needs_correction vs needs_correction
- ❌ `grant_00001__corr_missing_budget` _(remove_document: removed required document 'budget' (Itemised budget))_ — disp reject vs reject
- ❌ `grant_00001__corr_missing_registration` _(remove_document: removed required document 'registration_cert' (Registry extract))_ — disp reject vs reject
- ❌ `grant_00001__corr_over_budget` _(scale_number: scaled ['budget.row.equipment.amount_eur', 'budget.row.other.amount_eur', 'budget.row.outreach.amount_eur', 'budget.row.personnel.amount_eur', 'budget.totals.total'] by 1.6)_ — disp reject vs needs_correction
- ✅ `grant_00001__corr_sum_mismatch` _(set_field: set application_form.requested_total_eur = 89200)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_unregistered` _(set_field: set application_form.months_registered = 3)_ — disp reject vs reject
- ❌ `grant_00001__corr_unsigned` _(drop_signature: signature dropped (application_form.signature_present=false))_ — disp needs_correction vs reject
- ❌ `grant_00001__corr_wrong_period` _(set_field: set finance_statement.period = 'FY2024')_ — disp None vs None, parse: no JSON object in reply
- ✅ `grant_00001` — disp accept vs accept

## minimax-m2.7-highspeed · rule_extraction · 2026-08-16T14:20:38.790892+00:00

- ❌ `policy_foundation_v2` — disp None vs None
- ❌ `policy_grant_2026` — disp None vs None

## minimax-m2.7 · rule_extraction · 2026-08-16T14:16:09.677250+00:00

- ❌ `policy_foundation_v2` — disp None vs None
- ❌ `policy_grant_2026` — disp None vs None

## minimax-m3 · conformance · 2026-08-16T14:23:34.370634+00:00

- ✅ `grant_00001__corr_equipment_heavy` _(set_field: set budget.row.equipment.share_pct = 55.5)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_late_submission` _(shift_date: shifted application_form.submission_date: 2026-09-12 -> 2026-10-27)_ — disp needs_correction vs needs_correction
- ❌ `grant_00001__corr_missing_budget` _(remove_document: removed required document 'budget' (Itemised budget))_ — disp reject vs reject
- ✅ `grant_00001__corr_missing_registration` _(remove_document: removed required document 'registration_cert' (Registry extract))_ — disp reject vs reject
- ✅ `grant_00001__corr_over_budget` _(scale_number: scaled ['budget.row.equipment.amount_eur', 'budget.row.other.amount_eur', 'budget.row.outreach.amount_eur', 'budget.row.personnel.amount_eur', 'budget.totals.total'] by 1.6)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_sum_mismatch` _(set_field: set application_form.requested_total_eur = 89200)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_unregistered` _(set_field: set application_form.months_registered = 3)_ — disp reject vs reject
- ✅ `grant_00001__corr_unsigned` _(drop_signature: signature dropped (application_form.signature_present=false))_ — disp reject vs reject
- ✅ `grant_00001__corr_wrong_period` _(set_field: set finance_statement.period = 'FY2024')_ — disp needs_correction vs needs_correction
- ✅ `grant_00001` — disp accept vs accept

## minimax-m3 · rule_extraction · 2026-08-16T14:24:21.667519+00:00

- ❌ `policy_foundation_v2` — disp None vs None
- ❌ `policy_grant_2026` — disp None vs None

## minimax-m2.7 · conformance · 2026-08-16T14:38:10.691484+00:00

- ✅ `ace_0000` — disp needs_correction vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ✅ `ace_0002` — disp needs_correction vs needs_correction
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp reject vs needs_correction
- ❌ `ace_0005` — disp needs_correction vs accept
- ✅ `ace_0006` — disp reject vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ✅ `ace_0008` — disp needs_correction vs needs_correction
- ❌ `ace_0009` — disp reject vs accept
- ❌ `ace_0010` — disp accept vs needs_correction
- ✅ `ace_0011` — disp accept vs accept
- ✅ `ace_0012` — disp reject vs needs_correction
- ❌ `ace_0013` — disp needs_correction vs accept
- ✅ `ace_0014` — disp needs_correction vs needs_correction
- ✅ `ace_0015` — disp accept vs accept
- ❌ `ace_0016` — disp accept vs needs_correction
- ❌ `ace_0017` — disp reject vs accept
- ✅ `ace_0018` — disp reject vs needs_correction
- ❌ `ace_0019` — disp needs_correction vs accept
- ❌ `ace_0020` — disp accept vs needs_correction
- ✅ `ace_0021` — disp accept vs accept
- ❌ `ace_0022` — disp accept vs needs_correction
- ❌ `ace_0023` — disp reject vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ❌ `ace_0026` — disp accept vs needs_correction
- ❌ `ace_0027` — disp reject vs accept
- ✅ `ace_0028` — disp reject vs needs_correction
- ✅ `ace_0029` — disp accept vs accept

## minimax-m3 · conformance · 2026-08-16T14:51:19.748050+00:00

- ✅ `ace_0000` — disp reject vs needs_correction
- ✅ `ace_0001` — disp accept vs accept
- ✅ `ace_0002` — disp reject vs needs_correction
- ✅ `ace_0003` — disp accept vs accept
- ✅ `ace_0004` — disp needs_correction vs needs_correction
- ❌ `ace_0005` — disp None vs accept
- ❌ `ace_0006` — disp accept vs needs_correction
- ✅ `ace_0007` — disp accept vs accept
- ❌ `ace_0008` — disp accept vs needs_correction
- ✅ `ace_0009` — disp accept vs accept
- ❌ `ace_0010` — disp accept vs needs_correction
- ❌ `ace_0011` — disp needs_correction vs accept
- ✅ `ace_0012` — disp needs_correction vs needs_correction
- ❌ `ace_0013` — disp reject vs accept
- ❌ `ace_0014` — disp accept vs needs_correction
- ✅ `ace_0015` — disp accept vs accept
- ✅ `ace_0016` — disp needs_correction vs needs_correction
- ❌ `ace_0017` — disp reject vs accept
- ✅ `ace_0018` — disp needs_correction vs needs_correction
- ❌ `ace_0019` — disp needs_correction vs accept
- ❌ `ace_0020` — disp accept vs needs_correction
- ✅ `ace_0021` — disp accept vs accept
- ❌ `ace_0022` — disp accept vs needs_correction
- ✅ `ace_0023` — disp accept vs accept
- ❌ `ace_0024` — disp accept vs needs_correction
- ✅ `ace_0025` — disp accept vs accept
- ❌ `ace_0026` — disp accept vs needs_correction
- ❌ `ace_0027` — disp needs_correction vs accept
- ✅ `ace_0028` — disp needs_correction vs needs_correction
- ✅ `ace_0029` — disp accept vs accept

## glm-4.7-flash · conformance · 2026-08-16T17:44:58.346587+00:00

- ✅ `grant_00001__corr_equipment_heavy` _(set_field: set budget.row.equipment.share_pct = 55.5)_ — disp needs_correction vs needs_correction
- ❌ `grant_00001__corr_late_submission` _(shift_date: shifted application_form.submission_date: 2026-09-12 -> 2026-10-27)_ — disp reject vs needs_correction
- ✅ `grant_00001__corr_missing_budget` _(remove_document: removed required document 'budget' (Itemised budget))_ — disp reject vs reject
- ✅ `grant_00001__corr_missing_registration` _(remove_document: removed required document 'registration_cert' (Registry extract))_ — disp reject vs reject
- ❌ `grant_00001__corr_over_budget` _(scale_number: scaled ['budget.row.equipment.amount_eur', 'budget.row.other.amount_eur', 'budget.row.outreach.amount_eur', 'budget.row.personnel.amount_eur', 'budget.totals.total'] by 1.6)_ — disp reject vs needs_correction
- ✅ `grant_00001__corr_sum_mismatch` _(set_field: set application_form.requested_total_eur = 89200)_ — disp needs_correction vs needs_correction
- ✅ `grant_00001__corr_unregistered` _(set_field: set application_form.months_registered = 3)_ — disp reject vs reject
- ✅ `grant_00001__corr_unsigned` _(drop_signature: signature dropped (application_form.signature_present=false))_ — disp reject vs reject
- ✅ `grant_00001__corr_wrong_period` _(set_field: set finance_statement.period = 'FY2024')_ — disp needs_correction vs needs_correction
- ✅ `grant_00001` — disp accept vs accept

## glm-4.7-flash · rule_extraction · 2026-08-16T17:47:56.953256+00:00

- ❌ `policy_foundation_v2` — disp None vs None
- ❌ `policy_grant_2026` — disp None vs None

## glm-4.7-flash · conformance · 2026-08-16T18:58:40.320895+00:00

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
