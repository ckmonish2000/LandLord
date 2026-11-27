#!/usr/bin/env python3
"""Scaffold a new project with the landlord folder structure and practices.

Creates a monorepo with:
    backend/   FastAPI + SQLAlchemy (SQLite by default), one entity: users (auth),
               settings, tests (pytest) and Ruff
    frontend/  React + Vite + TypeScript: log in, sign up, a signed-in home page
    PRACTICES.md, README.md, .gitignore

The files come from scaffold_template/ next to this script. Placeholders in them
(__PROJECT_NAME__, __PROJECT_SLUG__) are replaced with the new project's name.

Usage:
    python scaffold_project.py <target_dir> [--name "My App"] [--install] [--git] [--force]

    --name      display name (default: from the folder name, "my-app" -> "My App")
    --install   run `uv sync` in backend/ and `npm install` in frontend/
    --git       run `git init` and make a first commit
    --force     allow a target folder that already has files in it

As a function:
    from scaffold_project import scaffold
    scaffold(Path("../my-app"), name="My App")
"""

from __future__ import annotations

import argparse
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_DIR = HERE / "scaffold_template"

# Text files get their placeholders replaced; anything else is copied as is.
TEXT_SUFFIXES = {".py", ".toml", ".md", ".ts", ".tsx", ".json", ".html", ".css", ".example", ".gitignore", ""}
SKIP_NAMES = {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "node_modules", "data", ".DS_Store"}


def slugify(name: str) -> str:
    """'My Rental App' -> 'my-rental-app' (used for package names)."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError(f"can't make a package name from {name!r}")
    return slug


def title_from_folder(folder: str) -> str:
    """'my-rental_app' -> 'My Rental App'."""
    return " ".join(w.capitalize() for w in re.split(r"[-_\s]+", folder) if w) or "New Project"


def _render(text: str, name: str, slug: str) -> str:
    return text.replace("__PROJECT_NAME__", name).replace("__PROJECT_SLUG__", slug)


def _copy_template(target: Path, name: str, slug: str) -> list[Path]:
    written = []
    for src in sorted(TEMPLATE_DIR.rglob("*")):
        rel = src.relative_to(TEMPLATE_DIR)
        if any(part in SKIP_NAMES for part in rel.parts) or src.is_dir():
            continue
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in TEXT_SUFFIXES or src.name.startswith("."):
            dst.write_text(_render(src.read_text(), name, slug))
        else:
            shutil.copy2(src, dst)
        written.append(rel)
    return written


def _write_env(target: Path) -> None:
    """backend/.env from .env.example, with a fresh random AUTH_SECRET."""
    example = (target / "backend/.env.example").read_text()
    env = re.sub(r"^AUTH_SECRET=.*$", f"AUTH_SECRET={secrets.token_hex(32)}", example, flags=re.M)
    (target / "backend/.env").write_text(env)


def _practices() -> str | None:
    """PRACTICES.md from the template, or from the repository this script lives in."""
    for candidate in (TEMPLATE_DIR / "PRACTICES.md", HERE / "PRACTICES.md"):
        if candidate.exists():
            return candidate.read_text()
    return None


def _run(cmd: list[str], cwd: Path) -> None:
    print(f"  $ {' '.join(cmd)}  (in {cwd.name}/)")
    subprocess.run(cmd, cwd=cwd, check=True)


def scaffold(
    target: Path,
    name: str | None = None,
    install: bool = False,
    git: bool = False,
    force: bool = False,
) -> Path:
    """Create a new project at `target`. Returns the project folder."""
    if not TEMPLATE_DIR.is_dir():
        raise FileNotFoundError(f"template folder not found: {TEMPLATE_DIR}")
    target = target.expanduser().resolve()
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(f"{target} is not empty (use --force to write into it)")

    name = name or title_from_folder(target.name)
    slug = slugify(name)
    target.mkdir(parents=True, exist_ok=True)

    written = _copy_template(target, name, slug)
    if (text := _practices()) is not None and not (target / "PRACTICES.md").exists():
        (target / "PRACTICES.md").write_text(text)
        written.append(Path("PRACTICES.md"))
    _write_env(target)

    print(f"Created {name} ({slug}) in {target}: {len(written)} files + backend/.env")
    if install:
        _run(["uv", "sync"], target / "backend")
        _run(["npm", "install"], target / "frontend")
    if git:
        _run(["git", "init", "-q"], target)
        _run(["git", "add", "-A"], target)
        _run(["git", "commit", "-q", "-m", "chore: scaffold project"], target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target", type=Path, help="folder to create the project in")
    parser.add_argument("--name", help='display name, e.g. "My App" (default: from the folder name)')
    parser.add_argument("--install", action="store_true", help="install backend and frontend dependencies")
    parser.add_argument("--git", action="store_true", help="git init and make a first commit")
    parser.add_argument("--force", action="store_true", help="write into a folder that already has files")
    args = parser.parse_args(argv)

    try:
        project = scaffold(args.target, args.name, args.install, args.git, args.force)
    except (FileExistsError, FileNotFoundError, ValueError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(
        "\nNext:\n"
        f"  cd {project}/backend && uv sync && uv run fastapi dev src/main.py\n"
        f"  cd {project}/frontend && npm install && npm run dev\n"
        f"  cd {project}/backend && uv run pytest"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
