"""Normalize provider usage without losing cache or reasoning token fields."""
from __future__ import annotations

from typing import Any


def _number(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _pick(source: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if source.get(key) is not None:
            return _number(source[key])
    return 0


def normalize_usage(usage: dict[str, Any] | None) -> dict[str, Any]:
    """Add stable counters while retaining the provider's raw usage.

    OpenAI-style prompt_tokens includes cached input. APIs exposing additive
    top-level input_tokens plus cache fields are treated separately.
    """
    raw = dict(usage or {})
    prompt_details = raw.get("prompt_tokens_details") or raw.get("input_tokens_details") or {}
    completion_details = raw.get("completion_tokens_details") or raw.get("output_tokens_details") or {}
    cache_read = _pick(prompt_details, "cached_tokens", "cache_read_input_tokens", "prompt_cache_hit_tokens")
    cache_read = cache_read or _pick(raw, "cache_read_input_tokens", "cache_read_tokens", "prompt_cache_hit_tokens")
    cache_write = _pick(prompt_details, "cache_creation_input_tokens", "cache_write_input_tokens", "prompt_cache_miss_tokens")
    cache_write = cache_write or _pick(raw, "cache_creation_input_tokens", "cache_write_input_tokens", "prompt_cache_miss_tokens")

    raw_input = raw.get("input_tokens")
    if raw_input is not None and ("prompt_tokens" not in raw or raw.get("prompt_tokens") is None):
        input_tokens = _number(raw_input) + cache_read + cache_write
        uncached_input = _number(raw_input)
        source = "input_tokens_plus_cache"
    else:
        input_tokens = _number(raw.get("prompt_tokens", raw_input))
        uncached_input = max(0, input_tokens - cache_read - cache_write)
        source = "prompt_tokens_with_cache_details"

    output_tokens = _number(raw.get("completion_tokens", raw.get("output_tokens")))
    total_tokens = _number(raw.get("total_tokens")) or input_tokens + output_tokens
    reasoning_tokens = _pick(completion_details, "reasoning_tokens") or _pick(raw, "reasoning_tokens")
    raw.update({
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_write_input_tokens": cache_write,
        "cache_input_tokens": cache_read + cache_write,
        "uncached_input_tokens": uncached_input,
        "reasoning_tokens": reasoning_tokens,
        "token_count_source": source,
    })
    return raw
