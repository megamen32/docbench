#!/usr/bin/env python3
"""Deliver an age-encrypted SSS secret to a named pipe without logging it."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen


def main(url: str, identity: str, fifo: str) -> int:
    encrypted = urlopen(url, timeout=30).read()
    with Path(fifo).open("wb") as output:
        return subprocess.run(
            ["age", "--decrypt", "--identity", identity],
            input=encrypted,
            stdout=output,
            check=False,
        ).returncode


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
