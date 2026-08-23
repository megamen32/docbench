# Russian-language supplementary benchmark

This self-contained 52-case add-on is deliberately separate from the standard
DocBench leaderboard. It measures the same document-verification contracts
with Russian-language human-readable material:

- `grant/cases/`: 10 translated grant-conformance cases;
- `policy/cases/`: 12 native Russian policy-rule extraction cases;
- `ace/cases/`: 30 translated ACE contract-conformance cases;
- `rulesets/`: the matching Russian rulesets.

Machine identifiers, numeric values, dates, severities, and gold outcomes are
preserved. `grant/errorgen_ru.yaml` is a generation plan, not a scored
case. A Russian leaderboard must contain fresh runs over these paths; English
baseline artifacts are not eligible.
