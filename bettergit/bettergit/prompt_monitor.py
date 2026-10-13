import asyncio
import json

from iterm2 import PromptMonitor, async_get_last_prompt

from .app_globals import TRIGGER_VAR, app_globals
from .git_poller import GitPoller
from .logger import logger
from .repo_status import RepoStatus
from .utils import find_git_root


async def _session_trigger(repo_status: RepoStatus):
    assert app_globals.app is not None
    logger.debug("Triggering session %s", repo_status.session_id)
    session_id = repo_status.session_id
    session = app_globals.app.get_session_by_id(session_id)
    if not session:
        return
    trigger_value = json.dumps(repo_status.render())
    logger.debug("%s: Triggering sb update with %s", session_id, trigger_value)
    await session.async_set_variable(TRIGGER_VAR, trigger_value)
    logger.debug("%s: Triggered", session_id)


async def _poll(poller: GitPoller) -> None:
    assert app_globals.connection is not None
    session_id = poller.session_id
    prompt = await async_get_last_prompt(app_globals.connection, session_id)
    logger.debug("%s: prompt is %s", session_id, prompt)
    if prompt is None:
        return
    cwd = prompt.working_directory
    logger.debug("%s: cwd is %s", session_id, cwd)
    if cwd is None:
        return
    logger.debug("%s: Finding git root (was %s)", session_id, poller.repo_root)
    poller.repo_root = find_git_root(cwd)
    logger.debug("%s: Git root at %s", session_id, poller.repo_root)
    if poller.repo_root is None:
        logger.debug("%s: No git root found", session_id)
        assert app_globals.app is not None
        session = app_globals.app.get_session_by_id(session_id)
        assert session is not None
        await session.async_set_variable(TRIGGER_VAR, '[""]')
        return
    await poller.collect()
    logger.debug("%s: Poller state: %s", session_id, poller)


async def prompt_monitor(session_id: str):
    logger.debug("Starting prompt monitor for session %s", session_id)
    assert app_globals.app is not None
    session = app_globals.app.get_session_by_id(session_id)
    logger.debug("%s: Session is %s", session_id, session)
    poller = GitPoller(session_id=str(session_id), update_trigger=_session_trigger)
    logger.debug("%s: Poller created: %s", session_id, poller)
    if not session:
        return
    try:
        assert app_globals.connection is not None
        async with PromptMonitor(app_globals.connection, session_id) as mon:
            logger.debug("%s: Prompt monitor started", session_id)
            while True:
                logger.debug("%s: Prompt monitor polling", session_id)
                try:
                    await _poll(poller)
                except Exception:  # noqa: BLE001
                    logger.exception("%s: Poll failed", session_id)
                logger.debug("%s: Prompt monitor waiting for next prompt", session_id)
                await mon.async_get()
                logger.debug("%s: Prompt monitor received next prompt", session_id)
    except asyncio.CancelledError:
        logger.debug("Ending session %s", session_id)
