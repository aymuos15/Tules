# Usage Guide

## Quick Start

### Installation

```bash
cd /home/localssk23/geminihack/Tules
pip install -r requirements.txt
chmod +x Tules.py Tules-sessions.py
ln -sf $(pwd)/Tules.py ~/.local/bin/Tules
ln -sf $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
```

## `Tules` - Background Agent Runner

### Run a single background task

```bash
# Auto-detects available provider (Claude or Gemini)
Tules run "analyze this codebase and find security vulnerabilities"

# Or explicitly choose a provider
Tules --provider claude run "analyze with Claude"
Tules --provider gemini run "analyze with Gemini"
```

**What happens:**
- Creates a new session with UUID
- Runs AI CLI in headless mode with permission bypass enabled
- Wraps execution in Docker sandbox
- Logs output to `~/<provider>/bg-agents/logs/<session-id>.log`
- Tracks session in `~/<provider>/bg-agents/sessions.json`
- Creates a git branch `<provider>-bg/<task>-<id>` (if in git repo)
- Returns immediately (runs in background)

### Run multiple tasks in parallel

```bash
Tules parallel \
  "analyze authentication code" \
  "review database queries for SQL injection" \
  "check for XSS vulnerabilities"
```

**What happens:**
- Spawns 3 separate background Claude processes
- Each runs independently with its own session ID
- All run simultaneously (not sequentially)

### List background agents

```bash
# Show only running agents
Tules list

# Show all agents (including completed)
Tules list --all
```

**Output:**
```
Background Agents
┏━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Session ID ┃ Status   ┃ Prompt     ┃ Started          ┃ Sandboxed  ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ a1b2c3d4   │ running  │ analyze... │ 2025-11-15 10:00 │ Yes        │
└────────────┴──────────┴────────────┴──────────────────┴────────────┘
```

### View logs

```bash
# Show last 50 lines (default)
Tules logs a1b2c3d4

# Show last 100 lines
Tules logs a1b2c3d4 -n 100

# Follow logs in real-time (like tail -f)
Tules logs a1b2c3d4 --follow
```

### Kill a running agent

```bash
Tules kill a1b2c3d4
```

### Schedule a task (experimental)

```bash
# Schedule daily at 9am
Tules schedule-task "0 9 * * *" "daily code review" --name "daily-review"

# Note: Scheduler daemon not yet implemented
# Use system cron instead for now
```

---

## `Tules-sessions` - Session Manager TUI

### View sessions for current directory

```bash
cd ~/my-project
Tules-sessions
```

**What happens:**
- Scans `~/.claude/projects/-home-user-my-project/` for `*.jsonl` files
- Shows interactive TUI with session list
- Arrow keys to navigate, Enter to view details

**Interactive controls:**
- `↑/↓` - Navigate sessions
- `Enter` or `v` - View session details
- `r` - Resume session (continues in current terminal)
- `f` - Fork session (create new branch from this session)
- `b` - Back to list (when in detail view)
- `q` - Quit

### View sessions for specific directory

```bash
Tules-sessions ~/geminihack
Tules-sessions /home/user/CAI4Soumya
```

### View all sessions (grouped by directory)

```bash
Tules-sessions --all
```

**Output:**
```
📁 Sessions for /home/localssk23/geminihack
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃    ┃ ID         ┃ Type     ┃ Summary    ┃ Date             ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│  > │ 71914264   │ MAIN     │ No summary │ 2025-11-15 10:29 │
│    │ agent-c1   │ AGENT    │ No summary │ 2025-11-15 09:46 │
└────┴────────────┴──────────┴────────────┴──────────────────┘

📁 Sessions for /home/localssk23/CAI4Soumya
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃    ┃ ID         ┃ Type     ┃ Summary    ┃ Date             ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│    │ a2b3c4d5   │ MAIN     │ Auth work  │ 2025-11-14 16:30 │
└────┴────────────┴──────────┴────────────┴──────────────────┘
```

### Filter sessions

```bash
# Show sessions since a date
Tules-sessions --since "2025-11-01"

# Search by summary content (regex)
Tules-sessions --search "authentication"

# Show only agent sessions
Tules-sessions --agents-only

# Show only main sessions
Tules-sessions --main-only

# Combine filters
Tules-sessions --since "2025-11-01" --search "auth" --main-only
```

### Non-interactive mode

```bash
# Just list sessions, no TUI
Tules-sessions --list
Tules-sessions ~/my-project --list
```

---

## Advanced Examples

### Background Code Review Workflow

```bash
# Start background review
Tules run "review all Python files for security issues and generate a report"

# List to get session ID
Tules list

# Follow logs to monitor progress
Tules logs a1b2c3d4 --follow

# When done, view the session
Tules-sessions
# (navigate to session, press 'v' to see details)
```

### Parallel Testing

```bash
Tules parallel \
  "run pytest and fix any failing tests" \
  "run eslint and fix linting errors" \
  "run mypy and fix type errors"

# Monitor all at once
Tules list --all
```

### Session Recovery

```bash
# View all sessions
Tules-sessions --all

# Find old session
Tules-sessions --search "authentication refactor"

# Resume the session (interactive TUI)
Tules-sessions
# (navigate to session, press 'r')

# Or fork to create a new branch
# (navigate to session, press 'f')
```

---

## File Locations

- **Background agent data:** `~/.claude/bg-agents/`
  - `sessions.json` - Session metadata
  - `logs/<session-id>.log` - Output logs
  - `schedules.json` - Scheduled tasks

- **Claude sessions:** `~/.claude/projects/<encoded-directory>/`
  - `<session-id>.jsonl` - Main session
  - `agent-<agent-id>.jsonl` - Agent session

---

## Notes

- **Sandboxing:** Requires `bubblewrap` on Linux. Install with `sudo apt install bubblewrap`
- **Permissions:** `--dangerously-skip-permissions` bypasses all permission prompts (use with caution)
- **Session encoding:** Directory `/home/user/project` becomes `-home-user-project`
- **Partial IDs:** Most commands accept partial session IDs (e.g., `a1b2` instead of full UUID)
