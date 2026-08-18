# docbench — agent instructions

## Secrets and key locations (CAREFUL — do not echo or commit)

This project ships benchmark results run against third-party LLM providers.
**No provider key is in this repository.** The audit below is the source of
truth for where keys live and how to inject them; do not paste any key in
chat, into argv, or into commit-bound files.

### MiniMax (MiniMax API, OpenAI-compatible)

- **Where**: `~/.config/docbench/env`, line `DOCBENCH_MINIMAX_API_KEY=…`
  (chmod 600, only readable by the owner). `DOCBENCH_MINIMAX_BASE_URL`
  optional override.
- **How the key was set**: user pasted the value in chat. Per
  `secrets-in-chat-protocol`, the only safe write path was a python heredoc
  with the literal as a string constant (no shell expansion, no `read -rsp`,
  no `cat .env`). That message is still in chat history / session DB / Telegram
  log, so **the key must be considered compromised and rotated** before any
  real production use. The current key works for benchmarks; rotate and
  overwrite the same file when convenient.
- **Verification of presence without printing**:
  `[[ -n "${DOCBENCH_MINIMAX_API_KEY:-}" ]] && echo set || echo missing`
- **Never**: echo the value, write it to any file inside the repo, pass it as
  argv, paste it back in chat, or include it in any log/telemetry.

### Z.ai (session coding plan, OpenAI-compatible via `api.z.ai/api/paas/v4`)

- **Where**: **nowhere on disk in this repo or in `~/.config/docbench/env`.**
  The token lives only in `~/.zcode/v2/config.json`, provider
  `builtin:zai-coding-plan`, field `options.apiKey` (key was already there
  before this project started — it is the user's own coding plan that funds
  the assistant session itself).
- **How it is consumed**:
  - Local runs: `export DOCBENCH_ZAI_API_KEY=$(python3 -c "
    import json,pathlib
    print(json.loads((pathlib.Path.home()/'~/.zcode/v2/config.json').read_text())
    ['provider']['builtin:zai-coding-plan']['options']['apiKey'])")` —
    resolves only in the launching process; no copy is persisted.
  - Container runs: `--env-file ~/.config/docbench/env` (does NOT include the
    z.ai token by default) plus `-e DOCBENCH_ZAI_API_KEY` if the caller
    exports it themselves; never baked into the image or its layers.
- **Why no on-disk copy**: the z.ai coding-plan token is already compromised by
  the user's session surface; rotating it requires going through Z.ai's
  account console. Writing it into a project-local file would put another
  secret-leak surface in front of it for no benefit.
- **Never**: copy the value from `config.json` into any file in the repo,
  into argv, into commit history, into chat, into logs. The launcher pattern
  above reads it from the user's own config; that is the only sanctioned read.

### General key-handling rules (apply to any future provider)

1. Add the provider to `docbench/models.yaml` (`base_url_env`, `base_url_default`,
   `api_key_env`). Set `api_key_env` to a `DOCBENCH_<PROVIDER>_*` name only;
   reuse the harness's `~/.config/docbench/env` for anything that has a stable
   API key.
2. Prefer reading from the harness session config (`~/.zcode/v2/config.json`)
   over re-entering the value. If the value must be cached, cache it in
   `~/.config/docbench/env` (chmod 600), never in the repo.
3. Every `key in chat = rotation expected`. Always recommend rotation once a
   benchmark campaign that needed that key is finished.
4. Quantisation: providers do not expose served quantisation via the API; pin
   provider + alias + date + the served-model id echoed back in each completion,
   and record `quantization = null` with a note in the run metadata.
5. If a leak-check ever fails on a sanitised transcript, do not upload — fix
   the regex and re-render. The public README has no secrets.

## Run metadata (what every run records)

`results.json` per run includes:
- `provider`, `provider_label`, `model`, `model_alias`
- `effort` (label), `request_extra` (exact body params sent)
- `quantization` (null + note when not exposed), `served_models`
- `price_source` (`assumed`/`placeholder` mark costs as estimates)
- per-case `usage.served_model`, latency, cost

Reproduce offline for free: `docbench run --bench <b> --model <m> --offline --cases <c>`.