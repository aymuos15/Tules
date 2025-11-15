# AI Background Agent Tools

Minimal Python tools for managing AI background agents and sessions.

**Supports both Claude Code and Gemini CLI backends** - automatically detects available providers or lets you choose.

## Installation

```bash
pip install -r requirements.txt
chmod +x claude-bg.py claude-sessions.py
ln -s $(pwd)/claude-bg.py ~/.local/bin/claude-bg
ln -s $(pwd)/claude-sessions.py ~/.local/bin/claude-sessions
```

## Tools

### `claude-bg` - Background Agent Runner

Run AI agents in headless sandboxed mode with no permission prompts.

```bash
# Run a single task in background (auto-detects provider)
claude-bg run "analyze this codebase and generate a report"

# Use specific provider
claude-bg --provider claude run "analyze code with Claude"
claude-bg --provider gemini run "analyze code with Gemini"

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

Interactive TUI for viewing and managing AI sessions (folder-based).

```bash
# Show sessions for current directory (auto-detects provider)
claude-sessions

# Use specific provider
claude-sessions --provider claude
claude-sessions --provider gemini

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
