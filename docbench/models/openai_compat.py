"""OpenAI-compatible chat/completions runner: retries, content-hash cache,
usage/cost accounting. Works with MiniMax and any compatible endpoint."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

import requests

from ..config import ModelSpec
from .base import Completion


class OpenAICompatRunner:
    def __init__(self, spec: ModelSpec, cache_dir: Path | None = None,
                 timeout: float = 180.0, max_retries: int = 6, offline: bool = False):
        self.spec = spec
        self.model_key = spec.key
        self.alias = spec.alias
        self.base_url = spec.base_url
        self._api_key = spec.api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.offline = offline
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- public -----------------------------------------------------------

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.0,
                 max_tokens: int = 8192, extra_body: dict[str, Any] | None = None) -> Completion:
        extra_body = extra_body or {}
        cache_key = self._cache_key(messages, temperature, max_tokens, extra_body)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        if self.offline:
            raise RuntimeError(
                "offline mode: no cache entry for this request "
                f"({cache_key[:12]}…); run once online to populate the cache"
            )
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return self._call(messages, temperature, max_tokens, cache_key, extra_body)
            except _Retryable as e:
                last_err = e
                time.sleep(min(2 ** attempt * 2.0, 45.0))
        raise RuntimeError(f"{self.model_key}: request failed after {self.max_retries} retries") from last_err

    # -- internals ----------------------------------------------------------

    def _call(self, messages, temperature, max_tokens, cache_key, extra_body=None) -> Completion:
        payload = {
            "model": self.alias,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if extra_body:
            payload.update(extra_body)
        t0 = time.monotonic()
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout,
        )
        latency = time.monotonic() - t0
        if resp.status_code in (429, 500, 502, 503, 504):
            raise _Retryable(f"HTTP {resp.status_code}")
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        text = ""
        for ch in data.get("choices", []):
            msg = ch.get("message", {})
            if msg.get("content"):
                text = msg["content"]
                break
        usage = data.get("usage", {}) or {}
        comp = Completion(
            text=text,
            usage={"prompt_tokens": usage.get("prompt_tokens"),
                   "completion_tokens": usage.get("completion_tokens")},
            latency_s=round(latency, 3),
            cost_usd=self._cost(usage),
            cost_is_estimate=str(self.spec.price_source or "").startswith(("assumed", "placeholder")),
            model=data.get("model") or self.alias,  # served variant id, if echoed
        )
        self._cache_put(cache_key, comp)
        return comp

    def _cost(self, usage: dict[str, Any]) -> Optional[float]:
        if self.spec.price_in is None or self.spec.price_out is None:
            return None
        tin = usage.get("prompt_tokens") or 0
        tout = usage.get("completion_tokens") or 0
        return tin / 1e6 * self.spec.price_in + tout / 1e6 * self.spec.price_out

    def _cache_key(self, messages, temperature, max_tokens, extra_body=None) -> str:
        # Empty extra must not change the key: keeps the pre-effort cache valid.
        blob = {"m": self.model_key, "msgs": messages, "t": temperature, "mt": max_tokens}
        if extra_body:
            blob["x"] = extra_body
        return hashlib.sha256(json.dumps(blob, sort_keys=True, ensure_ascii=False)
                              .encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Optional[Path]:
        return self.cache_dir / f"{key}.json" if self.cache_dir else None

    def _cache_get(self, key: str) -> Optional[Completion]:
        p = self._cache_path(key)
        if not p or not p.is_file():
            return None
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return Completion(cache_hit=True, **d)
        except (json.JSONDecodeError, TypeError):
            return None

    def _cache_put(self, key: str, comp: Completion) -> None:
        p = self._cache_path(key)
        if not p:
            return
        p.write_text(json.dumps({
            "text": comp.text, "usage": comp.usage, "latency_s": comp.latency_s,
            "cost_usd": comp.cost_usd, "cost_is_estimate": comp.cost_is_estimate,
            "model": comp.model,
        }, ensure_ascii=False), encoding="utf-8")


class _Retryable(Exception):
    pass
