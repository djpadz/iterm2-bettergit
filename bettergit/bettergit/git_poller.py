import asyncio
import dataclasses
import shutil
from asyncio import Future
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from os import defpath, environ, getenv, pathsep
from pathlib import Path
from typing import Any

from .config import get_config
from .logger import logger
from .repo_status import RepoStatus
from .utils import MyPathLike, find_git_roots

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

POLLING_INTERVAL = 10  # 5 minutes

last_poll: dict[Path, float] = {}

CollectionMethodReturnType = Mapping[str, Any]
CollectionMethod = Callable[[], Coroutine[Any, Any, CollectionMethodReturnType]]


class GitPoller:
    def __init__(
        self, session_id: str, update_trigger: Callable[[RepoStatus], Awaitable[Any]]
    ):
        self._repo_root: Path | None = None
        self.session_id = session_id
        self._update_trigger = update_trigger
        self._repo_status: RepoStatus | None = None
        self._fetch_future: Future[None] | None = None
        self._time_to_clear_repo_status = True
        self._collection_methods: list[CollectionMethod] = [
            self.collect_counts,
            self.collect_stashes,
            self.collect_current_branch,
            self.collect_repo_counts,
            self.collect_repo_state,
        ]

    async def update_trigger(self, repo_status: RepoStatus) -> None:
        logger.debug("%s: Calling update trigger with %s", self.session_id, repo_status)
        await self._update_trigger(repo_status)
        logger.debug("%s: Update trigger completed", self.session_id)

    async def clear_repo_status(self) -> None:
        self._time_to_clear_repo_status = False
        self.repo_status = None
        await self.update_trigger(self.repo_status)

    async def update_repo_status(self, new_values: dict[str, Any]) -> None:
        new_status = dataclasses.replace(self.repo_status, **new_values)
        logger.debug("%s: New status: %s", self.session_id, new_status)
        if new_status != self.repo_status:
            self.repo_status = new_status
            await self.update_trigger(self.repo_status)
        logger.debug("%s: Update repo status completed", self.session_id)

    @property
    def repo_status(self) -> RepoStatus:
        self._repo_status = self._repo_status or RepoStatus(session_id=self.session_id)
        return self._repo_status

    @repo_status.setter
    def repo_status(self, value: RepoStatus | None):
        self._repo_status = value

    @property
    def repo_root(self) -> Path | None:
        return self._repo_root

    @repo_root.setter
    def repo_root(self, value: MyPathLike | None):
        logger.debug("%s: Setting repo root to %s", self.session_id, value)
        new_value = Path(value).resolve() if value is not None else None
        if new_value != self._repo_root:
            logger.debug("%s: this is a change", self.session_id)
            self._time_to_clear_repo_status = True
            self._repo_root = new_value
            self._fetch_future = None
        logger.debug("%s: set root", self.session_id)

    async def _do_fetch(self) -> None:
        try:
            logger.debug("%s: Fetching", self.session_id)
            await self.update_repo_status({"fetching": True})
            logger.debug("%s: Fetching in %s", self.session_id, self.repo_root)
        except Exception as e:  # noqa: BLE001
            logger.error("%s: Fetching failed: %s", self.session_id, e)
        cur_root = self.repo_root
        assert cur_root is not None
        logger.debug("%s: Fetching in %s", self.session_id, cur_root)
        await self._run_git_command("fetch", "--quiet")
        last_poll[cur_root] = asyncio.get_event_loop().time()
        logger.debug("%s: Done fetching in %s", self.session_id, cur_root)
        await self.update_repo_status({"fetching": False})

    async def collect(self) -> None:
        logger.debug("%s: Collecting", self.session_id)
        if (
            self._time_to_clear_repo_status
            or self.repo_status.repo_root != self.repo_root
        ):
            await self.clear_repo_status()
        self.repo_status.repo_root = self.repo_root
        if self.repo_root is None:
            logger.debug("%s: No repo root", self.session_id)
            return
        logger.debug("%s: Repo root is %s", self.session_id, self.repo_root)
        if self._fetch_future is not None:
            await self._fetch_future
            self._fetch_future = None
        _, stdout = await self._run_git_command("remote", "show")
        if (
            stdout.strip()
            and (
                last_poll.setdefault(self.repo_root, 0) + POLLING_INTERVAL
                < asyncio.get_event_loop().time()
            )
            and self._fetch_future is None
        ):
            self._fetch_future = asyncio.create_task(self._do_fetch())
            logger.debug("%s: created: %s", self.session_id, self._fetch_future)
        logger.debug("%s: Running collection methods", self.session_id)
        results = await asyncio.gather(*(x() for x in self._collection_methods))
        res: CollectionMethodReturnType = {}
        for r in results:
            res.update(r)
        logger.debug("%s: Collection results: %s", self.session_id, res)
        # noinspection PyArgumentList
        await self.update_repo_status(res)
        logger.debug("%s: Collection complete", self.session_id)

    async def _run_command(
        self, command: str | MyPathLike, /, *args: str, cwd: MyPathLike
    ) -> tuple[int, str]:
        logger.debug("%s: Running %s %s in %s", self.session_id, command, args, cwd)
        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await proc.communicate()
        assert proc.returncode is not None
        logger.debug("%s: Done running %s %s", self.session_id, command, args)
        logger.debug("%s: rc: %d", self.session_id, proc.returncode)
        logger.debug("%s: stdout: %s", self.session_id, stdout)
        logger.debug("%s: stderr: %s", self.session_id, stderr)
        return proc.returncode, stdout.decode()

    async def _run_git_command(
        self, /, *args: str, cwd: MyPathLike | None = None
    ) -> tuple[int, str]:
        if cwd is None:
            cwd = self.repo_root
        assert cwd is not None
        logger.debug("%s: Running git %s in %s", self.session_id, args, cwd)
        git_binary = get_config("git_binary")
        logger.debug("%s: git binary is %s", self.session_id, git_binary)
        if not Path(git_binary).is_file() and shutil.which(git_binary) is None:
            raise FileNotFoundError(f"git binary {git_binary} not found")
        cur_path = getenv("PATH", defpath)
        logger.debug("%s: PATH is %s", self.session_id, cur_path)
        try:
            if Path(git_binary).is_absolute():
                new_path = cur_path.split(pathsep)
                new_path.append(str(Path(git_binary).parent))
                environ["PATH"] = pathsep.join(new_path)
            return await self._run_command(get_config("git_binary"), *args, cwd=cwd)
        finally:
            environ["PATH"] = cur_path

    @staticmethod
    async def _read_first_line_int(f: MyPathLike) -> int:
        return int(Path(f).read_text(encoding="ascii").splitlines()[0].strip())

    async def collect_repo_counts(self) -> dict[str, int | bool]:
        rc, stdout = await self._run_git_command(
            "status", "--porcelain", "--ignore-submodules", "-unormal"
        )
        if rc != 0:
            raise RuntimeError(f"git status failed: {stdout}")
        dirty = False
        untracked = 0
        modified = 0
        staged = 0
        deleted = 0
        for line in stdout.splitlines():
            dirty = True
            status = line[0:2]
            if status == "??":
                untracked += 1
            elif status == "AM":
                staged += 1
                modified += 1
            elif status == " M":
                modified += 1
            elif status == " D":
                deleted += 1
            elif status[0] == "A" or status[0] == "M" or status[0] == "D":
                staged += 1
        return {
            "dirty": dirty,
            "untracked": untracked,
            "modified": modified,
            "staged": staged,
            "deleted": deleted,
        }

    async def collect_current_branch(self) -> dict[str, str]:
        rc, stdout = await self._run_git_command("branch", "--show-current")
        if rc == 0 and stdout != "":
            return {"current_branch": stdout.strip()}
        rc, stdout = await self._run_git_command("rev-parse", "--short", "HEAD")
        if rc == 0:
            return {"current_branch": f"[{stdout.strip()}]"}  # detached HEAD
        raise RuntimeError(f"git branch failed: {stdout}")

    async def collect_stashes(self) -> dict[str, int]:
        rc, stdout = await self._run_git_command("stash", "list")
        if rc != 0:
            raise RuntimeError(f"git stash failed: {stdout}")
        return {"stashes": len(stdout.splitlines())}

    async def collect_counts(self) -> dict[str, int]:
        rc, stdout = await self._run_git_command(
            "rev-list", "--left-right", "--count", "HEAD...@{u}"
        )
        if rc == 0:
            push_count, pull_count = map(int, stdout.split())
        else:
            push_count, pull_count = 0, 0
        return {"push_count": push_count, "pull_count": pull_count}

    async def collect_repo_state(self) -> dict[str, int | str | None]:
        assert self.repo_root is not None
        _, git_dir = find_git_roots(self.repo_root)
        assert git_dir is not None
        rebase_dir = git_dir / "rebase-merge"
        state = None
        step = None
        total = None
        if rebase_dir.is_dir():
            state = f"REBASE-{'i' if (rebase_dir / 'interactive').exists() else 'm'}"
            step = await self._read_first_line_int(rebase_dir / "msgnum")
            total = await self._read_first_line_int(rebase_dir / "end")
        else:
            rebase_dir = git_dir / "rebase-apply"
            if rebase_dir.is_dir():
                step = await self._read_first_line_int(rebase_dir / "next")
                total = await self._read_first_line_int(rebase_dir / "last")
                if (rebase_dir / "rebasing").exists():
                    state = "REBASE"
                elif (rebase_dir / "applying").exists():
                    state = "AM"
                else:
                    state = "AM/REBASE"
            elif (git_dir / "MERGE_HEAD").exists():
                state = "MERGING"
            elif (git_dir / "CHERRY_PICK_HEAD").exists():
                state = "CHERRY-PICKING"
            elif (git_dir / "REVERT_HEAD").exists():
                state = "REVERTING"
            elif (git_dir / "BISECT_LOG").exists():
                state = "BISECTING"
        return {"state": state, "step": step, "total": total}
