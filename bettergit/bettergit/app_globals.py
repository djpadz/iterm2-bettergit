from dataclasses import dataclass

from iterm2 import App, Connection

APP_ID = "net.padz.iterm2.python_bettergit"
CWD_VAR = "user.python_bettergit_cwd"
TRIGGER_VAR = "user.python_bettergit_trigger"


@dataclass
class _globals:
    connection: Connection | None = None
    app: App | None = None


app_globals = _globals()
