from iterm2 import Connection, EachSessionOnceMonitor, async_get_app

from .app_globals import TRIGGER_VAR, app_globals
from .logger import logger
from .prompt_monitor import prompt_monitor
from .sb_component import sb_component, sb_component_callback


async def main(connection: Connection):
    app_globals.connection = connection
    app_globals.app = await async_get_app(connection)
    assert app_globals.app is not None
    logger.debug("BetterGit started in debug mode")
    logger.info("BetterGit started")
    logger.info("connection is %s", connection)
    logger.info("app is %s", app_globals.app)
    logger.info("Initializing trigger var")
    for window in app_globals.app.terminal_windows:
        for tab in window.tabs:
            for session in tab.all_sessions:
                await session.async_set_variable(TRIGGER_VAR, '[""]')
    logger.info("Registering status bar component")
    await sb_component.async_register(app_globals.connection, sb_component_callback)
    logger.info("Registering prompt monitor")
    await EachSessionOnceMonitor.async_foreach_session_create_task(
        app_globals.app, prompt_monitor
    )
    logger.info("BetterGit initialization complete")
