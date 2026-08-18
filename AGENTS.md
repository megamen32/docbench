# docbench — agent instructions

## Secrets and key locations (CAREFUL — do not echo or commit)

This project ships benchmark results run against third-party LLM providers.
**No provider key is in this repository.** The audit below is the source of
truth for where keys live and how to inject them; do not paste any key in
chat, into argv, or into commit-bound files.

### MiniMax (MiniMax API, OpenAI-compatible)

- **Where** (in order docbench reads):
  1. `./.env` (workspace, gitignored, per-project convenience) — preferred.
  2. `~/.config/docbench/env` (machine-wide, chmod 600) — fallback.
  3. Real process env (`export DOCBENCH_…=…`) — overrides both.
- **How the key was set**: user pasted the value in chat. Per
  `secrets-in-chat-protocol`, the only safe write path was a python heredoc
  with the literal as a string constant (no shell expansion, no `read -rsp`,
  no `cat .env`). That message is still in chat history / session DB / Telegram
  log, so **the key must be considered compromised and rotated** before any
  real production use. The current key works for benchmarks; rotate and
  overwrite the same file when convenient.
- **Verification of presence without printing**:
  `[[ -n "${DOCBENCH_MINIMAX_API_KEY:-}" ]] && echo set || echo missing`
- **Template**: copy `.env.example` to `.env`, fill values, `chmod 600`. The
  `.env` line is in `.gitignore` so no key can leak through git.
- **Never**: echo the value, write it to any file inside the repo (except the
  gitignored `.env` in workspace root), pass it as argv, paste it back in chat,
  or include it in any log/telemetry.

### Z.ai (session coding plan, OpenAI-compatible via `api.z.ai/api/paas/v4`)

- **Where** (in order docbench reads):
  1. `./.env` (workspace, gitignored) — convenience for local benchmark runs.
  2. `~/.config/docbench/env` — machine-wide fallback.
  3. Real process env — overrides both.
  If neither file has the key, the launcher pattern below can be used.
- **How it is consumed** (no .env file path):
  - `export DOCBENCH_ZAI_API_KEY=$(python3 -c "
    import json,pathlib
    print(json.loads((pathlib.Path.home()/'~/.zcode/v2/config.json').read_text())
    ['provider']['builtin:zai-coding-plan']['options']['apiKey'])")` —
    resolves only in the launching process; no copy is persisted if `.env`
    is absent.
  - Container runs: `--env-file ~/.config/docbench/env` and/or `-e
    DOCBENCH_ZAI_API_KEY` if the caller exports it themselves; never baked
    into the image or its layers.
- **Why an on-disk copy in `.env` is acceptable here**: `.env` is gitignored,
  chmod 600, lives only on this machine. The token was already exposed by
  being in `~/.zcode/v2/config.json`; putting it in a per-machine `.env`
  beside the code is no worse than the existing source, and it removes the
  need to reach into Z-code config on every run. Rotation still goes through
  Z.ai's account console.
- **Never**: commit `.env`, paste the value in chat, pass it as argv, or
  include it in any log/telemetry.

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

## Provider key map (full, no values)

| provider | env var | default base URL | source of key |
|---|---|---|---|
| MiniMax | `DOCBENCH_MINIMAX_API_KEY` | `https://api.minimax.io/v1` | chat-pasted; consider rotated |
| Z.ai (coding plan) | `DOCBENCH_ZAI_API_KEY` | `https://api.z.ai/api/paas/v4` | `~/.zcode/v2/config.json` provider `builtin:zai-coding-plan` |
| OmniRoute | `DOCBENCH_OMNIROUTE_API_KEY` | `https://omniroute.bezrabotnyi.com/v1` | `.env` (chat-pasted) |

Resolution order: `./.env` → `~/.config/docbench/env` → real process env.
Catalog models and full metadata contract: `docbench/models.yaml`.