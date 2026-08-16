from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

def _find_repo_root() -> Path:
    """Source layout wins; else the nearest cwd ancestor that looks like the
    repo (container installs run from site-packages but work under /app).
    pyproject.toml distinguishes a checkout from an installed package."""
    def is_repo(p: Path) -> bool:
        return (p / "docbench" / "models.yaml").is_file() and (p / "pyproject.toml").is_file()
    here = Path(__file__).resolve().parent.parent
    if is_repo(here):
        return here
    cwd = Path.cwd()
    for cand in (cwd, *cwd.parents):
        if is_repo(cand):
            return cand
    return here


REPO_ROOT = _find_repo_root()
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
        self.provider_label = provider_cfg.get("label", provider)
        env = resolved_env()
        base = env.get(provider_cfg["base_url_env"]) or provider_cfg.get("base_url_default")
        if not base:
            raise RuntimeError(f"provider {provider}: no base_url configured")
        self.base_url = base.rstrip("/")
        self.api_key_env = provider_cfg["api_key_env"]
        self.api_key = env.get(self.api_key_env)
        self.alias = model_cfg.get("alias", key)
        self.price_in = model_cfg.get("price_in_per_m")
        self.price_out = model_cfg.get("price_out_per_m")
        self.price_source = model_cfg.get("price_source")
        self.request_extra = model_cfg.get("request_extra") or {}
        self.effort_levels = model_cfg.get("effort_levels") or {}
        self.effort_default = model_cfg.get("effort_default")
        # Providers do not expose served quantization over the API; the honest
        # pin is provider + model + date + the served-model id they echo back.
        self.quantization = model_cfg.get("quantization")  # None unless declared

    def effort_extra(self, effort: str | None) -> dict[str, Any]:
        label = effort or self.effort_default
        if not self.effort_levels:
            return dict(self.request_extra)
        if label not in self.effort_levels:
            raise KeyError(
                f"model {self.key}: unknown effort {label!r}; "
                f"known: {sorted(self.effort_levels)}")
        extra = dict(self.request_extra)
        extra.update(self.effort_levels[label])
        return extra


def list_models() -> list[ModelSpec]:
    cat = load_catalog()
    out = []
    for pname, pcfg in cat.get("providers", {}).items():
        for mkey in pcfg.get("models", {}):
            out.append(ModelSpec(mkey, pname, pcfg, pcfg["models"][mkey]))
    return out


def resolve_model(key: str, *, allow_missing_key: bool = False) -> ModelSpec:
    for m in list_models():
        if m.key == key or m.alias == key:
            if not m.api_key and not allow_missing_key:
                raise RuntimeError(
                    f"model {key}: API key missing. Set {m.api_key_env} in the "
                    f"environment or in {USER_ENV_FILE} (chmod 600)."
                )
            return m
    known = ", ".join(m.key for m in list_models())
    raise KeyError(f"unknown model {key!r}; known models: {known}")
