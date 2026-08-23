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
from ..jsonutil import strip_think
from .base import Completion
from .usage import normalize_usage


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
            except (_Retryable, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_err = e
                time.sleep(min(2 ** attempt * 2.0, 45.0))
        raise RuntimeError(f"{self.model_key}: request failed after {self.max_retries} retries") from last_err

    # -- internals ----------------------------------------------------------

    def _request_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"}

    def _request_options(self) -> dict[str, Any]:
        return {}

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
            headers=self._request_headers(),
            json=payload,
            timeout=self.timeout,
            **self._request_options(),
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
                # Keep provider chain-of-thought out of every persisted result.
                # An unfinished think block becomes an empty reply, which the
                # benchmark retry path treats as non-final rather than a score.
                text = strip_think(msg["content"])
                break
        usage = normalize_usage(data.get("usage", {}) or {})
        comp = Completion(
            text=text,
            usage=usage,
            latency_s=round(latency, 3),
            cost_rub=self._cost(usage) if self.spec.price_currency == "RUB" else None,
            cost_usd=self._cost(usage) if self.spec.price_currency == "USD" else None,
            cost_is_estimate=(self.spec.price_currency == "RUB" and
                              self.spec.price_cache_read is None and
                              self.spec.price_cache_write is None),
            model=data.get("model") or self.alias,  # served variant id, if echoed
        )
        self._cache_put(cache_key, comp)
        return comp

    def _cost(self, usage: dict[str, Any]) -> Optional[float]:
        if self.spec.price_in is None or self.spec.price_out is None:
            return None
        usage = normalize_usage(usage)
        price_cache_read = getattr(self.spec, "price_cache_read", None)
        price_cache_write = getattr(self.spec, "price_cache_write", None)
        cache_read_price = self.spec.price_in if price_cache_read is None else price_cache_read
        cache_write_price = self.spec.price_in if price_cache_write is None else price_cache_write
        return ((usage["uncached_input_tokens"] * self.spec.price_in)
                + (usage["cache_read_input_tokens"] * cache_read_price)
                + (usage["cache_write_input_tokens"] * cache_write_price)
                + (usage["output_tokens"] * self.spec.price_out)) / 1e6

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
            comp = Completion(cache_hit=True, **d)
            comp.usage = normalize_usage(comp.usage)
            if comp.cost_rub is None and getattr(self.spec, "price_currency", "USD") == "RUB":
                comp.cost_rub = self._cost(comp.usage)
            if comp.cost_usd is None and getattr(self.spec, "price_currency", "USD") == "USD":
                comp.cost_usd = self._cost(comp.usage)
            return comp
        except (json.JSONDecodeError, TypeError):
            return None

    def _cache_put(self, key: str, comp: Completion) -> None:
        p = self._cache_path(key)
        if not p:
            return
        p.write_text(json.dumps({
            "text": comp.text, "usage": comp.usage, "latency_s": comp.latency_s,
            "cost_rub": getattr(comp, "cost_rub", None),
            "cost_usd": getattr(comp, "cost_usd", None),
            "cost_is_estimate": comp.cost_is_estimate,
            "model": comp.model,
        }, ensure_ascii=False), encoding="utf-8")


class _Retryable(Exception):
    pass
