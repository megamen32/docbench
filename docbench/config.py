from __future__ import annotations

import os
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_ENV_FILE = Path.home() / ".config" / "docbench" / "env"


def load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def resolved_env() -> dict[str, str]:
    """File env first, real process environment wins on top."""
    env = load_env_file(USER_ENV_FILE)
    env.update(dict(os.environ))
    return env


def load_catalog() -> dict:
    with open(REPO_ROOT / "docbench" / "models.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ModelSpec:
    def __init__(self, key: str, provider: str, provider_cfg: dict, model_cfg: dict):
        self.key = key
        self.provider = provider
        self.alias = model_cfg.get("alias", key)
        env = resolved_env()
        base = env.get(provider_cfg["base_url_env"]) or provider_cfg.get("base_url_default")
        if not base:
            raise RuntimeError(f"provider {provider}: no base_url configured")
        self.base_url = base.rstrip("/")
        self.api_key_env = provider_cfg["api_key_env"]
        self.api_key = env.get(self.api_key_env)
        self.price_in = model_cfg.get("price_in_per_m")
        self.price_out = model_cfg.get("price_out_per_m")
        self.price_source = model_cfg.get("price_source")


def list_models() -> list[ModelSpec]:
    cat = load_catalog()
    out = []
    for pname, pcfg in cat.get("providers", {}).items():
        for mkey in pcfg.get("models", {}):
            out.append(ModelSpec(mkey, pname, pcfg, pcfg["models"][mkey]))
    return out


def resolve_model(key: str) -> ModelSpec:
    for m in list_models():
        if m.key == key or m.alias == key:
            if not m.api_key:
                raise RuntimeError(
                    f"model {key}: API key missing. Set {m.api_key_env} in the "
                    f"environment or in {USER_ENV_FILE} (chmod 600)."
                )
            return m
    known = ", ".join(m.key for m in list_models())
    raise KeyError(f"unknown model {key!r}; known models: {known}")
