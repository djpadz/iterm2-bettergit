import json
from dataclasses import asdict, dataclass
from typing import Optional

from .config import get_config
from .logger import logger
from .utils import MyPathLike

LICENSE = """
Copyright 2023 Dj Padzensky

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.
"""


@dataclass(frozen=False, kw_only=True)
class RepoStatus:
    session_id: str
    fetching: bool = False
    repo_root: MyPathLike | None = None
    push_count: int | None = None
    pull_count: int | None = None
    current_branch: str | None = None
    dirty: bool | None = None
    untracked: int | None = None
    modified: int | None = None
    staged: int | None = None
    deleted: int | None = None
    stashes: int | None = None
    state: str | None = None
    step: int | None = None
    total: int | None = None

    def render(self) -> str | list[str]:
        logger.debug("%s: rendering %s", self.session_id, self)
        if self.repo_root is None:
            return ""
        if self.state:
            status_line = get_config("icon_status_other") + " " + self.state
            if self.step is not None and self.total is not None:
                status_line += f" ({self.step}/{self.total})"
            return status_line
        parts: list[str] = []
        part = ""
        if self.dirty:
            part += get_config("icon_status_dirty")
        elif self.push_count or self.pull_count:
            part += get_config("icon_status_push_or_pull")
        else:
            part += get_config("icon_status_clean")
        part += f" {self.current_branch}"
        logger.debug(
            "%s: push: %s pull: %s", self.session_id, self.push_count, self.pull_count
        )
        if self.push_count and self.push_count > 0:
            part += " " + get_config("icon_push_count") + f" {self.push_count}"
        if self.pull_count and self.pull_count > 0:
            part += " " + get_config("icon_pull_count") + f" {self.pull_count}"
        parts.append(part.strip())
        part = ""
        if self.modified and self.modified > 0:
            part += " " + get_config("icon_modified_count") + f" {self.modified}"
        if self.untracked:
            part += " " + get_config("icon_untracked_count") + f" {self.untracked}"
        if self.deleted:
            part += " " + get_config("icon_deleted_count") + f" {self.deleted}"
        parts.append(part.strip())
        part = ""
        if self.staged:
            part += " " + get_config("icon_staged_count") + f" {self.staged}"
        if self.stashes:
            part += " " + get_config("icon_stashes_count") + f" {self.stashes}"
        parts.append(part.strip())
        logger.debug("%s: parts: %s", self.session_id, parts)
        parts = [part for part in parts if part != ""]
        logger.debug("%s: parts+: %s", self.session_id, parts)
        if self.fetching:
            part = get_config("icon_fetching")
            parts.append(part)
        ret = [
            " \N{LEFT VERTICAL BOX LINE} ".join(parts[0:x])
            for x in range(1, len(parts) + 1)
        ]
        logger.debug("%s: rendered parts: %s", self.session_id, ret)
        return ret

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> Optional["RepoStatus"]:
        logger.info("from_json: %s", json_str)
        if not json_str.startswith("{"):
            return None
        return cls(**json.loads(json_str))

    @classmethod
    def exemplar(cls):
        return cls(
            session_id="exemplar",
            current_branch="main",
            repo_root="/path/to/repo",
            dirty=True,
            push_count=2,
            pull_count=5,
            modified=3,
            untracked=2,
            deleted=4,
            staged=10,
            stashes=3,
            state=None,
            step=None,
            total=None,
        ).render()[-1]
