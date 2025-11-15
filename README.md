# Tules - AI Background Agent Tools

Minimal Python tools for managing AI background agents and sessions.

**Supports both Claude Code and Gemini CLI backends** - automatically detects available providers or lets you choose.

## ⚡ Quick Install

Choose one method:

### 🚀 Method 1: Automated Install (Recommended)

```bash
git clone https://github.com/yourusername/Tules.git
cd Tules
./install.sh
```

The installer will:
- ✅ Check Python 3.8+ and dependencies
- ✅ Install required packages
- ✅ Create symlinks in `~/.local/bin`
- ✅ Validate PATH configuration
- ✅ Test installation

### 📦 Method 2: Pip Install

```bash
pip install git+https://github.com/yourusername/Tules.git
```

### 🔧 Method 3: Manual Install

```bash
git clone https://github.com/yourusername/Tules.git
cd Tules
pip install -r requirements.txt
chmod +x Tules.py Tules-sessions.py !
ln -s $(pwd)/Tules.py ~/.local/bin/Tules
ln -s $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
ln -s $(pwd)/! ~/.local/bin/!
```

### ✅ Verify Installation

```bash
Tules --help
Tules-sessions --help
\! --help
```

If commands are not found, ensure `~/.local/bin` is in your PATH.

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

## 🔧 Troubleshooting

### Commands not found after installation

**Problem**: `Tules: command not found` or `!: command not found`

**Solution**: Ensure `~/.local/bin` is in your PATH:

```bash
# Check if it's in your PATH
echo $PATH | grep -q "$HOME/.local/bin" && echo "✅ In PATH" || echo "❌ Not in PATH"

# Add to PATH (for bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Add to PATH (for zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Python version too old

**Problem**: `Python 3.8+ required, found 3.6`

**Solution**: Install Python 3.8 or higher:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.10

# macOS (with Homebrew)
brew install python@3.10
```

### Docker not installed

**Problem**: `Docker not found` warning

**Solution**: Docker is recommended but not strictly required. Install from:
- https://docs.docker.com/get-docker/

Without Docker, agents run locally without sandboxing.

### Permission denied errors

**Problem**: `Permission denied` when creating symlinks

**Solution**: Ensure you have write permissions to `~/.local/bin`:

```bash
mkdir -p ~/.local/bin
chmod u+w ~/.local/bin
```

### Symlink conflicts

**Problem**: `File exists (not a symlink): ~/.local/bin/Tules`

**Solution**: Remove the existing file first:

```bash
rm ~/.local/bin/Tules
./install.sh
```

### No AI provider available

**Problem**: `No AI provider available. Please install claude or gemini-cli.`

**Solution**: Install at least one AI CLI:

**Claude Code**:
```bash
# Follow instructions at: https://claude.com/code
```

**Gemini CLI**:
```bash
npm install -g @google/generative-ai-cli
```

## 🗑️ Uninstall

To remove Tules from your system:

```bash
# Using the installer
./install.sh --uninstall

# Or manually
rm ~/.local/bin/Tules ~/.local/bin/Tules-sessions ~/.local/bin/!
```

**Note**: This only removes symlinks. To completely clean up:

```bash
# Remove symlinks
./install.sh --uninstall

# Remove session data (optional)
rm -rf ~/.claude/bg-agents/
rm -rf ~/.gemini/bg-agents/

# Uninstall Python packages (optional)
pip uninstall -y rich click schedule
```
