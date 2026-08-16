#!/usr/bin/env bash
# Containerised verification: everything pinned except the LLM provider.
#
# Offline mode (default) — full determinism, NO network at all:
#   scripts/container_verify.sh offline minimax-m2.7 conformance cases/seed-grant
#
# Online mode — provider egress allowed; export DOCBENCH_*_API_KEY first
# (e.g. from ~/.config/docbench/env). The z.ai session token can be injected
# the same way docbench tests do; nothing is baked into the image.
#   scripts/container_verify.sh online glm-4.7-flash conformance cases/ace-test
#
# The response cache (var/cache) is shared with the host, so an online run
# populates the cache that offline replays later score deterministically.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:?usage: $0 offline|online MODEL BENCH CASES [extra docbench args...]}"
MODEL="${2:?model}"
BENCH="${3:?bench}"
CASES="${4:?cases dir or file}"
shift 4 || true

IMG=docbench:latest
docker build -q -t "$IMG" . >/dev/null

COMMON_ARGS=(
  --rm
  -u "$(id -u):$(id -g)"
  -v "$PWD/var/cache:/app/var/cache"
  -v "$PWD/var/container-runs:/app/var/runs"
)

case "$MODE" in
  offline)
    exec docker run --network none "${COMMON_ARGS[@]}" "$IMG" \
      run --bench "$BENCH" --model "$MODEL" --cases "$CASES" --offline "$@"
    ;;
  online)
    # Keys come from ~/.config/docbench/env via --env-file (KEY=VALUE format)
    # plus any DOCBENCH_* exported in this shell; they reach the container
    # process only, never the image or its layers.
    ENV_FILE_ARGS=()
    [ -f "$HOME/.config/docbench/env" ] && ENV_FILE_ARGS=(--env-file "$HOME/.config/docbench/env")
    exec docker run "${COMMON_ARGS[@]}" "${ENV_FILE_ARGS[@]}" \
      -e DOCBENCH_MINIMAX_API_KEY -e DOCBENCH_MINIMAX_BASE_URL \
      -e DOCBENCH_ZAI_API_KEY -e DOCBENCH_ZAI_BASE_URL \
      "$IMG" run --bench "$BENCH" --model "$MODEL" --cases "$CASES" "$@"
    ;;
  *) echo "unknown mode $MODE" >&2; exit 2 ;;
esac
