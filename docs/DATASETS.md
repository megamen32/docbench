# Datasets and licenses

Registry: `datasets/registry.yaml`. State after bootstrap: `datasets/MANIFEST.md`.

```bash
.venv/bin/docbench datasets list
.venv/bin/docbench datasets fetch --all          # disk-guarded (min 30 GB free)
.venv/bin/docbench datasets fetch --only varex
```

| source | what it is | local state |
|---|---|---|
| llamaindex/ExtractBench | 370 enterprise docs, doc+schema→JSON with grounding | HF download |
| ibm-research/VAREX | 1777 government forms, schema-per-document | HF download |
| opendatalab/CiteVQA | QA gold with page/bbox provenance (PDFs gated on ModelScope) | QA fetched |
| Fujitsu ACE | 4700 compliance scenarios over 633 real contracts, CC BY 4.0 | in clone + converted cases/ace-test |
| UCSB-NLP-Chang/CompliBench | guidelines + violations + harness | in clone |
| column-tax/tax-calc-bench | expert tax cases, strict correctness | in clone |
| databricks/officeqa (+pro-v2) | grounded financial QA | gated — needs HF_TOKEN |
| applicaai/kleister-charity | real UK charity reports | git-annex manual step |

Gated repos return 401 anonymously: accept terms on the HF dataset page, then
`huggingface-cli login` (or export `HF_TOKEN`) and rerun the fetch command.

ACE-derived cases in this repo (`cases/ace-test/`, `rulesets/ace-*.yaml`) are
redistributed under CC BY 4.0 with attribution — see `NOTICE`.
