# Tules Usage Guide

Complete command reference for Tules background agent tools.

## Installation

### Method 1: One-Line Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash
```

This downloads and runs the installer automatically. The installer will:
- Check Python 3.8+ and dependencies
- Install required packages
- Create symlinks in `~/.local/bin`
- Validate PATH configuration
- Test installation

### Method 2: Clone and Install

```bash
git clone https://github.com/aymuos15/Tules.git
cd Tules
./install.sh
```

### Method 3: Pip Install

```bash
pip install git+https://github.com/aymuos15/Tules.git
```

### Method 4: Manual Install

```bash
git clone https://github.com/aymuos15/Tules.git
cd Tules
pip install -r requirements.txt
chmod +x Tules.py Tules-sessions.py !
ln -s $(pwd)/Tules.py ~/.local/bin/Tules
ln -s $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
ln -s $(pwd)/! ~/.local/bin/!
```

### Verify Installation

```bash
Tules --help
Tules-sessions --help
\! --help
```

If commands are not found, ensure `~/.local/bin` is in your PATH.

---

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

## Provider System

Both tools support Claude Code and Gemini CLI:

### Auto-detection
By default, Tules tries Claude first, then Gemini.

### Explicit Selection
```bash
Tules --provider claude run "analyze this"
Tules --provider gemini run "analyze this"
Tules-sessions --provider claude
Tules-sessions --provider gemini
```

### Provider Differences

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Session resuming | ✅ Yes | ✅ Yes |
| Session forking | ✅ Yes | ❌ No |
| Custom session IDs | ✅ Yes | ❌ No |
| Permission bypass | `--dangerously-skip-permissions` | `-y` (YOLO mode) |
| Session storage | `~/.claude/projects/` | `~/.gemini/tmp/` |
| Session format | JSONL | JSON |

### Configuration

Sessions and logs stored in provider-specific directories:
- Claude: `~/.claude/bg-agents/`
- Gemini: `~/.gemini/bg-agents/`

---

## The `!` Command

Ultra-short wrapper for minimal typing:

```bash
# Run with Claude (default)
\! fix this bug

# Run with Gemini
\! !gemini analyze this code

# Run with Claude (explicit)
\! !claude refactor this

# List all sessions
\! list --all

# View logs
\! logs abc123

# Clear completed
\! clear

# Kill session
\! kill abc123
```

**Note:** Escape `!` in bash as `\!` due to history expansion.

---

## Troubleshooting

### Commands not found

**Problem:** `Tules: command not found`

**Solution:** Ensure `~/.local/bin` is in PATH:

```bash
# Check PATH
echo $PATH | grep -q "$HOME/.local/bin" && echo "✅ In PATH" || echo "❌ Not in PATH"

# Add to PATH (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Add to PATH (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Python version too old

**Problem:** `Python 3.8+ required, found 3.6`

**Solution:** Install Python 3.8+:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.10

# macOS (Homebrew)
brew install python@3.10
```

### Docker not installed

**Problem:** `Docker not found` warning

**Solution:** Docker is recommended but optional. Install from:
- https://docs.docker.com/get-docker/

Without Docker, agents run locally without sandboxing.

### No AI provider available

**Problem:** `No AI provider available`

**Solution:** Install at least one AI CLI:

**Claude Code:**
```bash
# Follow: https://claude.com/code
```

**Gemini CLI:**
```bash
npm install -g @google/generative-ai-cli
```

### Permission denied errors

**Problem:** `Permission denied` creating symlinks

**Solution:**

```bash
mkdir -p ~/.local/bin
chmod u+w ~/.local/bin
```

---

## Uninstall

```bash
# Using installer
./install.sh --uninstall

# Or manually
rm ~/.local/bin/Tules ~/.local/bin/Tules-sessions ~/.local/bin/!
```

Complete cleanup (optional):

```bash
./install.sh --uninstall
rm -rf ~/.claude/bg-agents/
rm -rf ~/.gemini/bg-agents/
pip uninstall -y rich click schedule
```

---

## Notes

- **Sandboxing:** Requires Docker. Auto-builds images on first run.
- **Permissions:** `--dangerously-skip-permissions` bypasses all prompts (use with caution)
- **Session encoding:** Directory `/home/user/project` becomes `-home-user-project`
- **Partial IDs:** Most commands accept partial session IDs (e.g., `a1b2` instead of full UUID)
