# Containerised verification

Everything except the LLM provider is pinned inside the image: Python version,
package version, cases, rulesets, prompts and scoring code. Providers receive
requests; nothing else leaves the container.

```bash
# offline: no network at all, scores replayed deterministically from var/cache
scripts/container_verify.sh offline minimax-m2.7 conformance cases/seed-grant

# online: provider egress; keys pass via --env-file ~/.config/docbench/env
scripts/container_verify.sh online glm-4.7-flash conformance cases/ace-test
```

- The response cache (`var/cache`) and run outputs (`var/container-runs`) are
  host mounts shared with local runs: an online container run populates the
  cache that offline replays later score without network (`--network none`).
- Keys are injected at container start only (`--env-file` / `-e`); they never
  enter the image or its layers.
- The image runs as an unprivileged user (`-u $(id -u):$(id -g)` on the host)
  and pins `PYTHONHASHSEED=0`.

## Egress control

Offline mode is fully sealed (`--network none`). Online mode uses the default
Docker bridge; to restrict egress to provider hosts only, attach a network with
`--iptables`-filtered rules or an explicit `--internal=false` network plus
host-level firewall allowlist for `api.minimax.io` / `api.z.ai` — the runner
makes no other network calls.
