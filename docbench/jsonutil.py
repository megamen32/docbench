"""Robust JSON extraction from LLM replies (reasoning models emit <think> blocks)."""
from __future__ import annotations

import json
import re
from typing import Any, Optional

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def strip_think(text: str) -> str:
    """Remove complete <think>…</think> blocks; an unclosed block means the
    reply was truncated inside reasoning — nothing usable remains."""
    if "</think>" in text:
        return _THINK_RE.sub("", text).strip()
    if text.lstrip().startswith("<think>"):
        return ""
    return text.strip()


def extract_json(text: str) -> Optional[dict[str, Any]]:
    """First balanced JSON object in the reply, after think/fence stripping.

    Reasoning models sometimes stop inside an unclosed <think> block right
    after writing the answer draft: fall back to the LAST balanced JSON
    object found anywhere in the raw text (final draft wins)."""
    cleaned = strip_think(text)
    for candidate in _candidates(cleaned):
        obj = _try_parse(candidate)
        if isinstance(obj, dict):
            return obj
    for candidate in reversed(_all_balanced_objects(text or "")):
        obj = _try_parse(candidate)
        if isinstance(obj, dict) and ("findings" in obj or "rules" in obj
                                      or "extracted" in obj or "ruleset_id" in obj):
            return obj
    return None


def _candidates(text: str) -> list[str]:
    out = []
    if not text:
        return out
    out.append(text)
    for m in _FENCE_RE.finditer(text):
        out.append(m.group(1).strip())
    balanced = _first_balanced_object(text)
    if balanced is not None:
        out.append(balanced)
    return out


_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def _try_parse(s: str) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError):
        pass
    repaired = _TRAILING_COMMA_RE.sub(r"\1", s)
    if repaired != s:
        try:
            return json.loads(repaired)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def _first_balanced_object(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _all_balanced_objects(text: str) -> list[str]:
    out: list[str] = []
    pos = 0
    while True:
        start = text.find("{", pos)
        if start == -1:
            return out
        depth = 0
        in_str = False
        esc = False
        end = None
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            return out
        out.append(text[start:end + 1])
        pos = end + 1
