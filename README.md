# Claude Background Agent Tools

Minimal Python tools for managing Claude Code background agents and sessions.

## Installation

```bash
pip install -r requirements.txt
chmod +x claude-bg.py claude-sessions.py
ln -s $(pwd)/claude-bg.py ~/.local/bin/claude-bg
ln -s $(pwd)/claude-sessions.py ~/.local/bin/claude-sessions
```

## Tools

### `claude-bg` - Background Agent Runner

Run Claude agents in headless sandboxed mode with no permission prompts.

```bash
# Run a single task in background
claude-bg run "analyze this codebase and generate a report"

# Schedule a task (cron syntax)
claude-bg schedule "0 9 * * *" "daily code review"

# Run multiple tasks in parallel
claude-bg parallel "task 1" "task 2" "task 3"

# List all background agents
claude-bg list

# View logs for a specific session
claude-bg logs <session-id>

# Kill a running agent
claude-bg kill <session-id>
```

### `claude-sessions` - Session Manager TUI

Interactive TUI for viewing and managing Claude Code sessions (folder-based).

```bash
# Show sessions for current directory
claude-sessions

# Show sessions for specific directory
claude-sessions ~/my-project

# Show all sessions (grouped by directory)
claude-sessions --all

# Filter sessions
claude-sessions --since "2025-01-01" --search "authentication"
claude-sessions --agents-only
claude-sessions --main-only

# Interactive commands:
# ↑/↓  - Navigate sessions
# r    - Resume session
# f    - Fork session
# v    - View session details
# q    - Quit
```

## Features

- **Sandboxed execution** - Runs agents in isolated environment (bubblewrap)
- **No permission prompts** - Auto-skips dangerous permissions
- **Folder-aware sessions** - Sessions scoped to working directory
- **Rich TUI** - Beautiful terminal interface with colors
- **Scheduling** - Cron-like task scheduling
- **Parallel execution** - Run multiple agents simultaneously

## Requirements

- Python 3.8+
- Claude Code CLI
- Linux with `bubblewrap` (for sandboxing)
