from dataclasses import dataclass

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

CONFIG_DEFAULTS: dict[str, str] = {
    "git_binary": "/usr/bin/git",
    "icon_fetching": "\N{WATCH}",
    "icon_status_other": "\u203c\ufe0f",  # Red double exclamation mark
    "icon_status_dirty": "\U0001f534",  # Red circle
    "icon_status_push_or_pull": "\U0001f7e1",  # Yellow circle
    "icon_status_clean": "\U0001f7e2",  # Green circle
    "icon_push_count": "\N{UPWARDS BLACK ARROW}",
    "icon_pull_count": "\N{DOWNWARDS BLACK ARROW}",
    "icon_modified_count": "\N{LOWER RIGHT PENCIL}",
    "icon_untracked_count": "\N{WARNING SIGN}",
    "icon_deleted_count": "\N{MINUS SIGN}",
    "icon_staged_count": "\N{CHECK MARK}",
    "icon_stashes_count": "\N{UP ARROWHEAD IN A RECTANGLE BOX}",
}


RUNNING_CONFIG: dict[str, str] = {}


def get_config_default(item: str):
    return CONFIG_DEFAULTS[item]


def get_config(item: str) -> str:
    return RUNNING_CONFIG.get(item, CONFIG_DEFAULTS[item])


def set_config(item: str, value: str):
    RUNNING_CONFIG[item] = value


@dataclass
class StringKnobConfig:
    key: str
    name: str
    placeholder: str | None = None


STRING_KNOB_CONFIGS: list[StringKnobConfig] = [
    StringKnobConfig("git_binary", "Git binary", get_config_default("git_binary")),
    StringKnobConfig("icon_status_other", "Icon: Status other"),
    StringKnobConfig("icon_status_dirty", "Icon: Status dirty"),
    StringKnobConfig("icon_status_push_or_pull", "Icon: Status push or pull"),
    StringKnobConfig("icon_status_clean", "Icon: Status clean"),
    StringKnobConfig("icon_push_count", "Icon: Push count"),
    StringKnobConfig("icon_pull_count", "Icon: Pull count"),
    StringKnobConfig("icon_modified_count", "Icon: Modified count"),
    StringKnobConfig("icon_untracked_count", "Icon: Untracked count"),
    StringKnobConfig("icon_deleted_count", "Icon: Deleted count"),
    StringKnobConfig("icon_staged_count", "Icon: Staged count"),
    StringKnobConfig("icon_stashes_count", "Icon: Stashes count"),
]
