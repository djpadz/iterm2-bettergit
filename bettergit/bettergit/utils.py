from os import PathLike
from pathlib import Path
from typing import TypeAlias

MyPathLike: TypeAlias = PathLike[str] | str | Path


def find_git_roots(path: MyPathLike) -> tuple[Path, Path] | tuple[None, None]:
    """
    Find the root of the git repository containing the given path,
    as well as the path to the .git directory.
    Returns a tuple of the repository root and the .git directory path if found,
    otherwise returns (None, None).

    These directories have to be returned separately, because of git worktrees
    and the possibility of the .git directory being a file pointing to another
    location.
    """
    p = Path(path)
    while True:
        if (p / ".git").is_dir():
            return (p, p / ".git")
        elif (p / ".git").is_file():
            for line in (p / ".git").read_text().splitlines():
                if line.startswith("gitdir:"):
                    return (p, Path(line[len("gitdir:") :].strip()).resolve())
        elif not p.name:
            break
        p = p.parent
    return (None, None)
