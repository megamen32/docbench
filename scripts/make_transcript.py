#!/usr/bin/env python3
"""Render a ZCode session transcript (sqlite db: session/message/part) into a
sanitized Markdown transcript.

Everything the model saw and produced is included: user texts, assistant
reasoning and text, every tool call with its input and output. Single tool
outputs are capped at TOOL_CAP characters (marked) to keep the public artifact
readable; credential-shaped strings are redacted BEFORE writing and a final
leak check must pass with zero matches, otherwise nothing is written.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

TOOL_CAP = 4000

SECRET_PATTERNS = [
    (re.compile(r"sk-cp-lmzmgv[A-Za-z0-9_\-]*"), "<REDACTED-KEY>"),
    (re.compile(r"sk-cp-[A-Za-z0-9_\-]{10,}"), "<REDACTED-KEY>"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{24,}"), "<REDACTED-KEY>"),
    (re.compile(r"adcb2[A-Za-z0-9_\-]{8,}"), "<REDACTED-TOKEN>"),
    (re.compile(r"(Authorization[\"':\s=]+Bearer\s+)[A-Za-z0-9._\-]{16,}"), r"\1<REDACTED>"),
    (re.compile(r"(x-api-key[\"':\s=]+)[A-Za-z0-9._\-]{16,}"), r"\1<REDACTED>"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "<REDACTED-TOKEN>"),
]
LEAK_CHECK = re.compile(
    r"sk-cp-lmzmgv|sk-cp-[A-Za-z0-9_\-]{10,}|adcb2[A-Za-z0-9_\-]{8,}|Bearer\s+[A-Za-z0-9._\-]{16,}|sk-[A-Za-z0-9_\-]{24,}")


def sanitize(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def cap(text: str) -> str:
    if len(text) <= TOOL_CAP:
        return text
    return text[:TOOL_CAP] + f"\n…[truncated {len(text) - TOOL_CAP} chars]"


def render_part(d: dict) -> str | None:
    t = d.get("type")
    if t == "text":
        return sanitize(str(d.get("text", "")))
    if t == "reasoning":
        body = d.get("text") or d.get("content") or ""
        return f"<details><summary>thinking</summary>\n\n{sanitize(str(body))}\n\n</details>"
    if t == "tool":
        name = d.get("tool", "?")
        state = d.get("state", {}) or {}
        inp = state.get("input", {})
        inp_s = json.dumps(inp, ensure_ascii=False) if not isinstance(inp, str) else inp
        out = state.get("output") or state.get("content") or ""
        if not isinstance(out, str):
            out = json.dumps(out, ensure_ascii=False)
        status = state.get("status", "?")
        return (f"**tool `{name}` ({status})**\n\n"
                f"- input: `{cap(sanitize(inp_s))}`\n"
                f"- output:\n\n```\n{cap(sanitize(out))}\n```")
    return None  # step-start/step-finish/timeline/file are structural noise


def render_session(con, sid: str, out: list[str]) -> None:
    msgs = con.execute(
        "select id, sequence, data from message where session_id=? order by sequence", (sid,)
    ).fetchall()
    for mid, seq, data in msgs:
        d = json.loads(data)
        role = d.get("role", "?")
        model = d.get("modelID") or ""
        head = f"\n## [{role}" + (f" · {model}" if model else "") + "]"
        parts = con.execute(
            "select data from part where message_id=? order by sequence", (mid,)
        ).fetchall()
        rendered = [render_part(json.loads(p[0])) for p in parts]
        rendered = [r for r in rendered if r]
        if not rendered:
            continue
        out.append(head)
        out.extend(rendered)


def main(db_path: Path, sid: str, dst: Path) -> None:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    out = [
        "# docbench — full session transcript (sanitized)",
        "",
        f"Session `{sid}` rendered from the local ZCode transcript db. User texts, "
        f"assistant reasoning (collapsed), tool calls with inputs and outputs are "
        f"included; single tool outputs are capped at {TOOL_CAP} characters. "
        "All credential-shaped strings are redacted; a leak check must pass "
        "with zero matches before the file is written.",
        "",
    ]
    render_session(con, sid, out)
    children = [r[0] for r in con.execute(
        "select id from session where parent_id=?", (sid,))]
    for i, ch in enumerate(children, 1):
        out.append(f"\n---\n\n# Appendix {i}: subagent session {ch}")
        render_session(con, ch, out)

    text = "\n".join(out)
    leaks = LEAK_CHECK.findall(text)
    if leaks:
        print(f"FATAL: {len(leaks)} secret-shaped strings survived redaction; "
              "nothing written", file=sys.stderr)
        sys.exit(1)
    dst.write_text(text, encoding="utf-8")
    print(f"wrote {dst} ({dst.stat().st_size / 1e6:.1f} MB, "
          f"1 main + {len(children)} subagent sessions), leak check passed")


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
