#!/usr/bin/env bash
# Reproducible bootstrap: clone external benchmark sources (depth 1) into external/.
set -u
cd "$(dirname "$0")/.."
mkdir -p external
repos=(
  run-llama/ExtractBench
  FujitsuResearch/Fujitsu-Assessing-Compliance-in-Enterprise-Dataset
  UCSB-NLP-Chang/CompliBench
  udibarzi/varex-bench
  opendatalab/CiteVQA
  applicaai/kleister-charity
  column-tax/tax-calc-bench
  databricks/officeqa
)
for r in "${repos[@]}"; do
  name=$(basename "$r")
  [ -d "external/$name" ] && { echo "SKIP $r"; continue; }
  git clone --depth 1 "https://github.com/$r" "external/$name" && echo "OK $r" || echo "FAIL $r"
done
