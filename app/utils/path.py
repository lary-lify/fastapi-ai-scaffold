from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def find_project_root(marker_files=None) -> Path:
    """Walk up from this file to the project root.

    A directory is considered the root if it contains any marker file
    (.env, pyproject.toml, requirements.txt, .git). Falls back to the
    directory three levels above this file (project / app / utils / path.py).
    """
    if marker_files is None:
        marker_files = [".env", "pyproject.toml", "requirements.txt", ".git"]

    current = Path(__file__).resolve().parent
    while True:
        if any((current / m).exists() for m in marker_files):
            return current
        parent = current.parent
        if parent == current:  # reached filesystem root
            break
        current = parent
    return Path(__file__).resolve().parent.parent.parent
