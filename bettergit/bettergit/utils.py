from os import PathLike
from pathlib import Path
from typing import TypeAlias

MyPathLike: TypeAlias = PathLike[str] | str | Path


def find_git_root(path: MyPathLike) -> Path | None:
    p = Path(path)
    while True:
        if (p / ".git").is_dir():
            return p
        if not p.name:
            break
        p = p.parent
    return None
