# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

This repository contains standalone Python CLI tools for managing **Claude Code and Gemini CLI** background agents, instant responses, and sessions:

1. **`Tules.py`** (aliased as `T`) - Run AI agents in headless Docker-sandboxed mode with automatic permission bypass
2. **`Tules-instant.py`** (aliased as `Ti`) - Get instant AI responses with rich markdown rendering and syntax highlighting
3. **`Tules-sessions.py`** (aliased as `Ts`) - Interactive TUI for viewing and managing AI sessions, scoped by working directory

All tools support both **Claude Code** and **Gemini CLI** backends with automatic provider detection. Dependencies: Rich (TUI), Click (CLI), and a provider abstraction layer (`ai_provider.py`).

## Installation and Setup

**Recommended**: Use the automated installer:
```bash
./install.sh
```

**Or manually**:
```bash
# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x Tules.py Tules-instant.py Tules-sessions.py

# Create symlinks (tools are installed to ~/.local/bin/)
ln -sf $(pwd)/Tules.py ~/.local/bin/Tules
ln -sf $(pwd)/Tules.py ~/.local/bin/T
ln -sf $(pwd)/Tules-instant.py ~/.local/bin/Tules-instant
ln -sf $(pwd)/Tules-instant.py ~/.local/bin/Ti
ln -sf $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
ln -sf $(pwd)/Tules-sessions.py ~/.local/bin/Ts
```

**First-time Docker setup**: `Tules` will automatically build Docker images (`tules-claude:latest`, `tules-gemini:latest`) on first run.

## Multi-Provider Support

### Provider Abstraction Layer (`ai_provider.py`)

All tools use a provider abstraction that supports both **Claude Code** and **Gemini CLI**:

**Auto-detection logic**:
1. Try Gemini first (default provider)
2. Fall back to Claude if Gemini not found
3. Can be explicitly set with `--provider` flag (e.g., `--provider claude`)

**Provider-specific differences**:

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Session resuming | ✅ Yes (`--resume`) | ✅ Yes (`-r`) |
| Session forking | ✅ Yes (`--fork-session`) | ❌ No |
| Custom session IDs | ✅ Yes | ❌ Auto-generated |
| Permission bypass | `--dangerously-skip-permissions` | `-y` (YOLO mode) |
| Session storage | `~/.claude/projects/<encoded-path>/` | `~/.gemini/tmp/<hash>/chats/` |
| Session format | JSONL | JSON |
| Path encoding | Replace `/` with `-` | SHA-256 hash |

**Data Storage**:
- Claude: `~/.claude/bg-agents/`
- Gemini: `~/.gemini/bg-agents/`

## Architecture

### `Tules-instant` - Instant AI Response Tool

Provides quick AI responses without Docker overhead. Runs provider CLI commands directly (`gemini -p` or `claude -p`) and renders output with syntax highlighting via `tui_renderer.py`.

Usage examples:
```bash
Ti "what is 2+2?"
Ti --provider claude "explain async/await"
echo "write a haiku" | Ti --stdin
```

### `Tules` - Background Agent Runner

Docker-based sandboxing with log capture. Key implementation details:
- Must run as non-root in Docker (Claude Code requirement)
- Config file `~/.claude.json` must be explicitly mounted
- Session tracking uses OS process PID (`os.kill(pid, 0)`)
- Data storage: `~/.{provider}/bg-agents/`

### `Tules-sessions` - Session Manager TUI

Interactive TUI for session management:
- Path encoding: Replace `/` with `-` for Claude sessions
- Session format: JSONL (Claude) or JSON (Gemini)
- Actions: Resume (`r`), Fork (`f`), View details (`v`), View logs (`l`)
- Filtering: `--since`, `--agents-only`, `--main-only`

## Testing the Tools

```bash
# Instant responses
Ti "what is 2+2?"
echo "explain git rebase" | Ti --stdin

# Background agents
Tules run "what is 2+2?"
Tules list --all
Tules logs <session-id>

# Session management
Ts --list
Ts  # Interactive TUI
```

## Development Guidelines

### Adding Commands to `Tules`
1. Use Click decorator: `@cli.command()`
2. Use `console.print()` with Rich formatting
3. Follow existing patterns: Table for lists, Panel for single results

### TUI Renderer (`tui_renderer.py`)
- Code theme: `monokai` (change in `Syntax()` call)
- Modify `split_markdown_and_code()` for new block types
- Update `render_blocks()` for custom styling

### Docker Mounts
Must mount: workspace, `~/.claude`, `~/.claude.json`, Claude binary
Run as: `--user {uid}:{gid}` with `-e HOME={home}`

## Known Limitations

1. **TUI**: Unix-only (requires `termios`), falls back to static mode on non-TTY
2. **Sandboxing**: Docker-only (bubblewrap support removed)
3. **Gemini**: Session forking not supported (Claude Code only)
4. **Log viewing**: Background agent sessions only
