# AI Background Agent Tools

Minimal Python tools for managing AI background agents and sessions.

**Supports both Claude Code and Gemini CLI backends** - automatically detects available providers or lets you choose.

## Installation

```bash
pip install -r requirements.txt
chmod +x Tules.py Tules-sessions.py !
ln -s $(pwd)/Tules.py ~/.local/bin/Tules
ln -s $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
ln -s $(pwd)/! ~/.local/bin/!
```

## Quick Start: The `!` Command

Ultra-short wrapper for running background agents with minimal typing:

```bash
# Run with Claude (default)
\! fix this bug

# Run with Gemini
\! !gemini analyze this code

# List all sessions (from all providers)
\! list

# View logs
\! logs abc123

# Clear completed sessions
\! clear
```

**Note:** You need to escape `!` in bash as `\!` because `!` is used for history expansion. The command is still very short!

### `!` Command Syntax

- **`\! <prompt>`** - Run task with Claude (default provider)
- **`\! !gemini <prompt>`** - Run task with Gemini
- **`\! !claude <prompt>`** - Run task with Claude (explicit)
- **`\! list [--all]`** - List sessions
- **`\! logs <session-id>`** - View session logs
- **`\! clear`** - Clear completed sessions
- **`\! kill <session-id>`** - Kill running session

## Tools

### `Tules` - Background Agent Runner

Run AI agents in headless sandboxed mode with no permission prompts.

```bash
# Run a single task in background (auto-detects provider)
Tules run "analyze this codebase and generate a report"

# Use specific provider
Tules --provider claude run "analyze code with Claude"
Tules --provider gemini run "analyze code with Gemini"

# Schedule a task (cron syntax)
Tules schedule "0 9 * * *" "daily code review"

# Run multiple tasks in parallel
Tules parallel "task 1" "task 2" "task 3"

# List all background agents
Tules list

# View logs for a specific session
Tules logs <session-id>

# Kill a running agent
Tules kill <session-id>
```

### `Tules-sessions` - Session Manager TUI

Interactive TUI for viewing and managing AI sessions (folder-based).

```bash
# Show sessions for current directory (auto-detects provider)
Tules-sessions

# Use specific provider
Tules-sessions --provider claude
Tules-sessions --provider gemini

# Show sessions for specific directory
Tules-sessions ~/my-project

# Show all sessions (grouped by directory)
Tules-sessions --all

# Filter sessions
Tules-sessions --since "2025-01-01" --search "authentication"
Tules-sessions --agents-only
Tules-sessions --main-only

# Interactive commands:
# ↑/↓  - Navigate sessions
# r    - Resume session
# f    - Fork session (Claude only - Gemini doesn't support forking)
# v    - View session details
# q    - Quit
```

## Features

- **Multi-provider support** - Works with both Claude Code and Gemini CLI
- **Auto-detection** - Automatically finds available AI provider
- **Sandboxed execution** - Runs agents in isolated Docker containers
- **No permission prompts** - Auto-skips permission prompts (YOLO mode)
- **Folder-aware sessions** - Sessions scoped to working directory
- **Git branch isolation** - Each task runs in its own git branch
- **Rich TUI** - Beautiful terminal interface with colors
- **Session management** - View, resume, and fork sessions
- **Scheduling** - Cron-like task scheduling

## Requirements

- Python 3.8+
- At least one of:
  - **Claude Code CLI** (`claude`)
  - **Gemini CLI** (`gemini`)
- Docker (for sandboxed execution)
- Linux/macOS (Windows not tested)

## Provider System

The tools automatically detect which AI CLI is available on your system:

1. **Auto-detection** (default): Tries Claude first, then Gemini
2. **Explicit selection**: Use `--provider claude` or `--provider gemini`

### Provider Differences

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Session resuming | ✅ Yes | ✅ Yes |
| Session forking | ✅ Yes | ❌ No |
| Custom session IDs | ✅ Yes | ❌ No (auto-generated) |
| Permission bypass | `--dangerously-skip-permissions` | `-y` (YOLO mode) |
| Session storage | `~/.claude/projects/` | `~/.gemini/tmp/` |
| Session format | JSONL | JSON |

### Configuration

Sessions and logs are stored in provider-specific directories:
- Claude: `~/.claude/bg-agents/`
- Gemini: `~/.gemini/bg-agents/`
