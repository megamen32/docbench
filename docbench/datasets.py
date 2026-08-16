"""Sidecar: dataset registry + disk-guarded fetching."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from .config import REPO_ROOT

REGISTRY_PATH = REPO_ROOT / "datasets" / "registry.yaml"
DATA_ROOT = REPO_ROOT / "datasets" / "data"
EXTERNAL_ROOT = REPO_ROOT / "external"


def registry_entries() -> list[dict[str, Any]]:
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f).get("entries", [])


def entry_dir(e: dict[str, Any]) -> Path:
    if e["source_type"] == "hf":
        return DATA_ROOT / e["name"]
    return EXTERNAL_ROOT / e["external_dir"]


def local_state(e: dict[str, Any]) -> str:
    d = entry_dir(e)
    if e["source_type"] == "annex":
        annex_dir = d / ".git" / "annex" / "objects"
        populated = 0
        if annex_dir.is_dir():
            populated = sum(1 for _ in annex_dir.rglob("SHA256E-*"))
        linked = 0
        docs = d / "documents"
        if docs.is_dir():
            linked = sum(1 for p in docs.glob("*.pdf") if not p.is_symlink())
        return f"annex: {populated} objects, {linked} materialized pdfs"
    if not d.is_dir():
        return "missing"
    n_files = sum(1 for _ in d.rglob("*") if _.is_file())
    return f"present ({n_files} files)"


def _free_bytes() -> int:
    return shutil.disk_usage(str(REPO_ROOT)).free


def _hf_size_gb(repo_id: str) -> float:
    from huggingface_hub import HfApi
    info = HfApi().repo_info(repo_id, repo_type="dataset", files_metadata=True)
    return sum(f.size or 0 for f in info.siblings) / 1e9


def fetch_entry(e: dict[str, Any], min_free_gb: float = 30.0) -> Path:
    st = e["source_type"]
    if st == "in_repo":
        d = entry_dir(e)
        if not d.is_dir():
            raise FileNotFoundError(f"{e['name']}: expected clone at {d}; run scripts/fetch_external.sh")
        print(f"{e['name']}: already in clone {d}")
        return d
    if st == "annex":
        raise RuntimeError(
            f"{e['name']}: git-annex dataset. Install git-annex, then in external/{e['external_dir']} "
            f"run ./annex-get-all-from-s3.sh (remote {e.get('annex_remote')})"
        )
    if st == "hf":
        from huggingface_hub import snapshot_download
        size = _hf_size_gb(e["repo_id"])
        free = _free_bytes() / 1e9
        if free - size < min_free_gb:
            raise RuntimeError(
                f"{e['name']}: needs ~{size:.1f} GB but only {free:.1f} GB free "
                f"(min_free_gb={min_free_gb}); raise --min-free-gb or free disk"
            )
        print(f"{e['name']}: downloading {e['repo_id']} (~{size:.2f} GB, free {free:.0f} GB)")
        dest = snapshot_download(
            repo_id=e["repo_id"], repo_type="dataset",
            local_dir=DATA_ROOT / e["name"], max_workers=8,
        )
        print(f"{e['name']}: done -> {dest}")
        return Path(dest)
    raise ValueError(f"unknown source_type {st!r}")
