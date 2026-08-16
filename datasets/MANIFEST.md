# Dataset manifest — state after bootstrap (2026-08-16)

| name | status | size | where |
|---|---|---|---|
| extractbench | ✅ downloaded | 811 MB | `datasets/data/extractbench/` |
| varex | ✅ downloaded | 1.6 GB | `datasets/data/varex/` |
| citevqa (QA + provenance gold) | ✅ downloaded | 6.2 MB | `datasets/data/citevqa/` |
| tax-calc-bench | ✅ in clone | 290 MB | `external/tax-calc-bench/` |
| ace (Fujitsu) | ✅ in clone | 80 MB (train 76 + test 4) | `external/Fujitsu-Assessing-Compliance-in-Enterprise-Dataset/` |
| complibench | ✅ in clone | data/{airlines,healthcare,insurance} | `external/CompliBench/` |
| kleister-charity | ⚠️ needs git-annex | PDFs on S3 | install git-annex → `external/kleister-charity/annex-get-all-from-s3.sh` |
| citevqa (PDFs) | ⚠️ gated | ~GBs | approval-gated on ModelScope `risemds/CiteVQA_PDF` |
| officeqa | ⛔ gated | 5.4 GB | HF `databricks/officeqa`: accept terms + `HF_TOKEN` → `docbench datasets fetch --only officeqa` |
| officeqa-pro-v2 | ⛔ gated | 14.1 GB | HF `databricks/officeqa-pro-v2`: accept terms + `HF_TOKEN` → `docbench datasets fetch --only officeqa-pro-v2` |

Gated repos return `401` for anonymous requests; there is no HF token on this
machine (`~/.cache/huggingface/token` absent). After `huggingface-cli login`
(or exporting `HF_TOKEN`), rerun:

```bash
.venv/bin/docbench datasets fetch --only officeqa --only officeqa-pro-v2
```

Anonymous HF downloads were also IP-rate-limited (429) mid-batch; VAREX
completed on a retry with `HF_HUB_DISABLE_XET=1`.
