#!/usr/bin/env python3
"""Scaffold generator for the fastapi-ai-scaffold project.

Copies this repository into a fresh target directory and replaces the
``__PROJECT_NAME__`` placeholder with the chosen project name.

Usage:
    python scripts/scaffold.py --target /path/to/new_project --name my_project
"""
import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "logs", "__pycache__", ".venv", "venv", ".pytest_cache", ".ruff_cache"}
SKIP_EXTS = {".pyc", ".db"}


def render(text: str, name: str) -> str:
    return text.replace("__PROJECT_NAME__", name)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a new project from this scaffold.")
    ap.add_argument("--target", "-t", required=True, help="Target directory (created if missing).")
    ap.add_argument("--name", "-n", default=None, help="Project name (default: target dir name).")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    name = args.name or target.name

    if not REPO_ROOT.exists():
        print(f"[ERROR] Repo root not found: {REPO_ROOT}", file=sys.stderr)
        return 1

    target.mkdir(parents=True, exist_ok=True)
    written = 0
    for src in sorted(REPO_ROOT.rglob("*")):
        if src.is_dir():
            continue
        if any(part in SKIP_DIRS for part in src.parts):
            continue
        if src.suffix in SKIP_EXTS:
            continue
        if target in (src, *src.parents):
            continue
        rel = src.relative_to(REPO_ROOT)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            dst.write_text(render(src.read_text(encoding="utf-8"), name), encoding="utf-8")
        except UnicodeDecodeError:
            dst.write_bytes(src.read_bytes())
        written += 1

    tpl = target / ".env.template"
    if tpl.exists() and not (target / ".env").exists():
        shutil.copyfile(tpl, target / ".env")

    print(f"[OK] Project '{name}' created at {target} ({written} files)")
    print(f"\nNext steps:")
    print(f"  cd {target}")
    print(f"  cp .env.template .env   # then edit secrets")
    print(f"  pip install -r requirements.txt")
    print(f"  python main.py          # http://localhost:8000/docs")
    print(f"  # or: docker compose up -d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
