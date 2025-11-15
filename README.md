![Team](assests/team.png)

# Tules

AI CLI toolkit for Claude Code and Gemini CLI with background agents, instant responses, and session management.

Three powerful tools in one package:
- **Tules (T)**: Background agents in Docker with automatic permission bypass
- **Tules-instant (Ti)**: Instant AI responses with rich markdown rendering
- **Tules-sessions (Ts)**: Interactive session browser and manager

## Quick Install

**One-line install (public repos):**
```bash
curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash
```

**Clone and install (recommended for private repos):**
```bash
git clone https://github.com/aymuos15/Tules.git
cd Tules
./install.sh
```

**Uninstall:**
```bash
./install.sh --uninstall
```

**Troubleshooting?** See [INSTALL.md](INSTALL.md) for detailed installation instructions and troubleshooting.

## Usage

### Instant Responses (New!)

Get quick AI answers with beautiful formatting:

```bash
# Quick questions (use Tules-instant or Ti - they're the same)
Ti "what is 2+2?"
Ti "explain Python decorators"

# Code explanations with syntax highlighting
Ti "show me a quicksort implementation in Python"

# Specific provider
Ti --provider claude "write a haiku about coding"

# Pipe from stdin
echo "explain git rebase" | Ti --stdin
```

**Note:** `Ti` is a short alias for `Tules-instant` - instant, rich-formatted AI responses!

### Background Agents

For long-running tasks in Docker:

```bash
# Run background task (use Tules or T - they're the same)
Tules run "analyze this codebase"
T run "analyze this codebase"

# Run with specific provider (Claude)
Tules --provider claude run "explain this code"
T --provider claude run "explain this code"

# List running agents
Tules list
T list

# View logs
Tules logs <session-id>
```

**Note:** `T` is a short alias for `Tules` - background agent runner!

### Session Management

Browse and manage AI sessions:

```bash
# Manage sessions (use Tules-sessions or Ts - they're the same)
Tules-sessions
Ts

# List sessions for current directory
Tules-sessions --list
Ts --list

# Filter agent sessions only
Tules-sessions --agents-only
Ts --agents-only
```

**Note:** `Ts` is a short alias for `Tules-sessions` - session browser and manager!

## Features

### Tules-instant (Ti)
- **Rich Markdown Rendering** - Beautiful formatted output with syntax highlighting
- **Code Highlighting** - Language-specific syntax coloring for code blocks
- **No Docker Overhead** - Direct CLI execution for instant responses
- **Stdin Support** - Pipe prompts from other commands
- **Multi-provider** - Auto-detect Gemini or Claude

### Tules (T)
- **Background Agents** - Run long tasks in Docker containers
- **Docker Sandboxing** - Fully isolated execution environment
- **Auto Permissions** - Skip permission prompts automatically
- **Log Streaming** - Real-time log capture and viewing
- **Session Tracking** - Monitor running and completed agents

### Tules-sessions
- **Interactive Browser** - TUI for browsing sessions
- **Session Resume** - Continue previous conversations
- **Session Forking** - Branch from existing sessions
- **Log Viewing** - Inspect agent logs without leaving TUI
- **Smart Filtering** - Filter by date, type, content

### Universal
- **Multi-provider** - Gemini CLI and Claude Code support
- **Auto-detection** - Automatically finds available AI provider (defaults to Gemini)
- **Provider Selection** - Explicit `--provider` flag for control

## Requirements

- Python 3.8+
- Gemini CLI (`gemini`) or Claude Code CLI (`claude`)
- Docker (recommended)

## Documentation

- **[USAGE.md](USAGE.md)** - Complete command reference and examples
- **[CLAUDE.md](CLAUDE.md)** - Technical architecture details

## Uninstall

```bash
./install.sh --uninstall
```
