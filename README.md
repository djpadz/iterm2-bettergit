# [iterm2-bettergit](https://github.com/djpadz/iterm2-bettergit)

_An enhanced git status bar widget for [iTerm2](https://iterm2.com)_

## Features
- Displays the following information in the iTerm2 status bar:
    - Quick indicator of the current branch status:
      - `🟢` Branch is clean
      - `🌕` Branch is in sync, but there are pulls and/or pushes available.
      - `🔴` Branch is out of sync, and/or there are uncommited changes.
    - Current branch name
    - `⬆︎` Number of commits ahead of the remote
    - `⬇`︎ Number of commits behind the remote
    - `✎`︎ Number of unstaged changed files
    - `⚠︎` Number of untracked files
    - `−` Number of unstaged deleted files
    - `✓` Number of staged files
    - `⮹`️ Number of stashes
- Also has a special mode for rebasing, merging, cherry-picking, reversion, or bisection.

## Installation
1. Download the latest release from the [releases page](https://github.com/djpadz/iterm2-bettergit/releases).
2. Double-click it to install it in iTerm2. Tell it to autolaunch.
3. Add it to your status bar (iTerm2 → Settings… → Profiles → Session → Configure Status Bar)
4. If Python BetterGit doesn't appear in the components box (you may have to scroll down), then restart iTerm2 and try again.
