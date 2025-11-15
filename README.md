# Tules

Background agent runner for Claude Code and Gemini CLI.

Run AI agents in headless Docker-sandboxed mode with automatic permission bypass.

## Quick Install

**One-line install:**
```bash
curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash
```

**Or clone and install:**
```bash
git clone https://github.com/aymuos15/Tules.git
cd Tules
./install.sh
```

## Usage

```bash
# Run background task
Tules run "analyze this codebase"

# Run with specific provider
Tules --provider gemini run "explain this code"

# List running agents
Tules list

# View logs
Tules logs <session-id>

# Manage sessions
Tules-sessions
```

**Ultra-short wrapper:**
```bash
\! fix this bug
\! !gemini analyze this code
\! list
```

## Features

- **Multi-provider** - Claude Code and Gemini CLI support
- **Auto-detection** - Automatically finds available AI provider
- **Docker sandboxing** - Isolated execution environment
- **No prompts** - Auto-skips permission prompts
- **Session management** - View, resume, and fork sessions

## Requirements

- Python 3.8+
- Claude Code CLI (`claude`) or Gemini CLI (`gemini`)
- Docker (recommended)

## Documentation

- **[USAGE.md](USAGE.md)** - Complete command reference and examples
- **[CLAUDE.md](CLAUDE.md)** - Technical architecture details

## Uninstall

```bash
./install.sh --uninstall
```
