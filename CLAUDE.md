# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains standalone Python CLI tools for managing **Claude Code and Gemini CLI** background agents and sessions:

1. **`Tules.py`** (aliased as `?`) - Run AI agents in headless Docker-sandboxed mode with automatic permission bypass
2. **`Tules-sessions.py`** - Interactive TUI for viewing and managing AI sessions, scoped by working directory

All tools support both **Claude Code** and **Gemini CLI** backends with automatic provider detection. They are designed to be minimal, single-file executables that rely only on Rich (TUI), Click (CLI), and a provider abstraction layer (`ai_provider.py`).

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
chmod +x Tules.py Tules-sessions.py

# Create symlinks (tools are installed to ~/.local/bin/)
ln -sf $(pwd)/Tules.py ~/.local/bin/Tules
ln -sf $(pwd)/Tules.py ~/.local/bin/?
ln -sf $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
```

**First-time Docker setup**: `Tules` will automatically build Docker images (`tules-claude:latest`, `tules-gemini:latest`) on first run.

**One-line install from GitHub**:
```bash
curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash
```

## Multi-Provider Support

### Provider Abstraction Layer (`ai_provider.py`)

All tools use a provider abstraction that supports both **Claude Code** and **Gemini CLI**:

**Auto-detection logic**:
1. Try Claude first (`~/.local/bin/claude`)
2. Fall back to Gemini if Claude not found
3. Can be explicitly set with `--provider` flag

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

### `Tules` - Background Agent Runner

**Key Design Pattern**: Docker-based sandboxing with log capture via `docker logs -f`

**Execution Flow**:
1. Generate UUID for session
2. Check Docker availability and build image if needed
3. Run Claude in Docker container with:
   - Non-root user (required for `--dangerously-skip-permissions`)
   - Volume mounts: workspace, `~/.claude`, `~/.claude.json`, Claude binary
   - `--output-format text` for stdout capture
4. Spawn background process to stream `docker logs` to file
5. Track session metadata in `~/.claude/bg-agents/sessions.json`

**Critical Implementation Details**:
- **Must run as non-root in Docker**: Claude Code rejects `--dangerously-skip-permissions` when running as root
- **Log capture**: Uses separate `docker logs -f <container>` process piped to log file (not direct stdout redirect)
- **Config file mount**: `~/.claude.json` must be explicitly mounted (not covered by `~/.claude` mount)
- **Session tracking**: Uses OS process PID to determine if agents are still running (`os.kill(pid, 0)`)

**Data Storage**:
- Session metadata: `~/.claude/bg-agents/sessions.json`
- Logs: `~/.claude/bg-agents/logs/<session-id>.log`
- Schedules: `~/.claude/bg-agents/schedules.json`

### `Tules-sessions` - Session Manager TUI

**Key Design Pattern**: Folder-based session discovery with path encoding

**Directory Path Encoding**:
- Claude stores sessions at `~/.claude/projects/<encoded-path>/`
- Encoding: Replace `/` with `-` (e.g., `/home/user/project` → `-home-user-project`)
- Decoding: Replace `-` with `/`

**Session File Format** (JSONL):
- First line typically contains: `{"type":"summary","summary":"...","leafUuid":"..."}`
- Subsequent lines: Individual messages with `{"type":"user"|"assistant","message":{...},"timestamp":"..."}`
- Agent sessions: Filename starts with `agent-`

**Interactive TUI**:
- Uses `termios` for raw keyboard input (Unix-only)
- TTY detection: Gracefully falls back to static list mode when stdin is not a TTY
- Arrow key navigation with escape sequence parsing (`\x1b[A` = up, `\x1b[B` = down)
- Actions: Resume (`r`), Fork (`f`), View details (`v`), **View logs (`l`)**, Back (`b`), Quit (`q`)

**Session Detail View Improvements**:
- Shows ALL messages in conversation (not just first 5)
- 1000 characters per message (instead of 200)
- Message numbering: "Message 1 - USER:", "Message 2 - ASSISTANT:"
- Character count indicators when content is truncated

**Log Viewing** (`l` key):
- Shows last 100 lines from `~/.{provider}/bg-agents/logs/{session-id}.log`
- Only available for background agent sessions
- Real-time inspection without leaving TUI

**Filtering and Search**:
- Date filters: ISO format (`--since "2025-01-01"`)
- Content search: Regex on summary field
- Type filters: `--agents-only`, `--main-only`

## Testing the Tools

```bash
# Test background agent with default provider (Claude)
Tules run "what is 2+2?"

# Test with specific provider
Tules --provider gemini run "what is 2+2?"

# Check it ran
Tules list --all

# View output
Tules logs <session-id>

# Test session viewer (shows sessions for current directory)
Tules-sessions --list

# Test the ? alias (same as Tules)
? run "quick test task"
? --provider gemini run "test with gemini"

# Clear test sessions (specify provider)
Tules --provider claude clear --force
Tules --provider gemini clear --force
```

**Note**: Test with both providers if available to ensure multi-provider support works correctly.

## Common Modifications

### Adding a New Command to `Tules`

1. Add Click decorator: `@cli.command()`
2. Define function with Click arguments/options
3. Keep docstring concise (examples only in main `cli()` docstring)
4. Use `console.print()` with Rich formatting for output
5. Follow existing patterns: Table for lists, Panel for single results

### Modifying Docker Configuration

**Dockerfile location**: `./Dockerfile` (in repo root)

**Current mounts** (in `Tules.py`):
```python
'-v', f'{cwd}:/workspace'                    # Working directory
'-v', f'{home}/.claude:{home}/.claude'       # Claude config dir
'-v', f'{home}/.claude.json:{home}/.claude.json'  # Config file
'-v', f'{home}/.local/bin/claude:/usr/local/bin/claude:ro'  # Binary
'-v', f'{home}/.local/share/claude:{home}/.local/share/claude:ro'  # Installation
```

**Important**: Always run as `--user {uid}:{gid}` and set `-e HOME={home}` env var.

### Session Discovery Logic

The `find_sessions_for_directory()` function in `Tules-sessions.py`:
- Takes absolute path, encodes it, looks in `~/.claude/projects/<encoded>/`
- Returns `Session` objects (dataclass-like) with parsed metadata
- Sorts by timestamp (newest first)

To modify filtering: Update `filter_sessions()` function with additional criteria.

## Known Limitations

1. **Scheduler daemon**: Not implemented - `daemon` command exists but doesn't run (use system cron instead)
2. **Interactive TUI**: Requires `termios` (Unix-only, won't work on Windows). Gracefully falls back to static mode when TTY not available.
3. **Docker-only sandboxing**: Removed bubblewrap support in favor of Docker
4. **Session summary**: Most sessions show "No summary" (depends on AI CLI version storing summary in first line)
5. **Gemini limitations**: Session forking not supported (Claude Code only feature)
6. **Log viewing**: Only available for background agent sessions (regular interactive sessions don't generate log files)
