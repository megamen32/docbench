# Configuration

## Providers and keys

Providers are OpenAI-compatible `chat/completions` endpoints declared in
`docbench/models.yaml`. Keys resolve from the real environment first, then
from `~/.config/docbench/env` (chmod 600, `KEY=VALUE` lines, never committed):

```
DOCBENCH_MINIMAX_API_KEY=...
DOCBENCH_MINIMAX_BASE_URL=https://api.minimax.io/v1   # optional override
DOCBENCH_ZAI_API_KEY=...
```

Add a provider by adding a block to `models.yaml` with `base_url_env`,
`base_url_default`, `api_key_env` and a `models:` map.

## Reasoning effort / thinking level

Each model entry may declare `effort_levels` (label → extra request-body
params) and `effort_default`. Examples:

```yaml
glm-4.7-flash:
  effort_levels:
    provider-default: {}                              # no param sent
    thinking:        {thinking: {type: enabled}}
    no_thinking:     {thinking: {type: disabled}}
  effort_default: provider-default
```

Run with `--effort <label>`; every run records the resolved label and the exact
params in `results.json` (`effort`, `request_extra`). Effort changes the
response-cache key, so different efforts never share cached replies.

## Quantization honesty

Providers do **not** expose the served quantization over the API. docbench
therefore pins what can be pinned: `provider`, `model_alias`, the request
params, the run date, and the `served_models` ids the provider echoes back in
each completion. `results.json.quantization` stays `null` unless you declare a
known value in the catalog.

## Pricing honesty

`price_source` values starting with `assumed`/`placeholder` mark the cost
columns as estimates; replace them with invoiced numbers before publishing
cost claims built on this repo.
