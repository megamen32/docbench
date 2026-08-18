from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


@dataclass
class Completion:
    text: str
    usage: dict[str, Any] = field(default_factory=dict)
    latency_s: float = 0.0
    cost_rub: Optional[float] = None
    cost_usd: Optional[float] = None  # legacy compatibility for old fixtures
    cost_is_estimate: bool = False
    cache_hit: bool = False
    model: str = ""


class Runner(Protocol):
    """Minimal model surface used by benchmarks."""

    model_key: str

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.0,
                 max_tokens: int = 8192) -> Completion: ...
