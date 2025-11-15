# Installation Guide

Complete installation instructions and troubleshooting for Tules.

## Installation Methods

### Method 1: One-line Install (Public Repositories)

The fastest way to install from a public GitHub repository:

```bash
curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash
```

**How it works:**
1. Downloads the installation script directly from GitHub
2. Automatically detects it's a remote install
3. Clones the repository to a temporary location
4. Moves the repository to `~/.tules` (permanent location)
5. Installs dependencies and creates symlinks pointing to `~/.tules`

**Limitations:**
- Only works for **public** repositories
- Requires `git` to be installed
- Needs active internet connection

### Method 2: Clone and Install (Recommended)

Best for private repositories or if you want to inspect the code first:

```bash
git clone https://github.com/aymuos15/Tules.git
cd Tules
./install.sh
```

**For private repositories with SSH:**
```bash
git clone git@github.com:aymuos15/Tules.git
cd Tules
./install.sh
```

### Method 3: Manual Installation

If the automated installer doesn't work, you can install manually:

```bash
# 1. Clone the repository
git clone https://github.com/aymuos15/Tules.git
cd Tules

# 2. Install Python dependencies
pip install --user -r requirements.txt

# 3. Make scripts executable
chmod +x Tules.py Tules-instant.py Tules-sessions.py

# 4. Create installation directory
mkdir -p ~/.local/bin

# 5. Create symlinks
ln -sf $(pwd)/Tules.py ~/.local/bin/Tules
ln -sf $(pwd)/Tules.py ~/.local/bin/T
ln -sf $(pwd)/Tules-instant.py ~/.local/bin/Tules-instant
ln -sf $(pwd)/Tules-instant.py ~/.local/bin/Ti
ln -sf $(pwd)/Tules-sessions.py ~/.local/bin/Tules-sessions
ln -sf $(pwd)/Tules-sessions.py ~/.local/bin/Ts

# 6. Add to PATH (if not already there)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Requirements

- **Python 3.8+** (required)
- **pip** (required)
- **Docker** (recommended for background agents, optional for instant responses)
- **git** (required for remote installation)
- **Claude Code or Gemini CLI** (at least one required)

## Troubleshooting

### Issue: `curl` command fails with 404

**Cause:** The repository is private or the raw URL is incorrect.

**Solution:** Use Method 2 (clone and install):
```bash
git clone git@github.com:aymuos15/Tules.git
cd Tules
./install.sh
```

### Issue: "Command not found" after installation

**Cause:** `~/.local/bin` is not in your PATH.

**Solution:**
1. Add to your shell config file:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
   ```

2. Reload your shell:
   ```bash
   source ~/.bashrc  # or source ~/.zshrc
   ```

3. Or restart your terminal

### Issue: "Permission denied" when running scripts

**Cause:** Scripts are not executable.

**Solution:**
```bash
cd Tules
chmod +x Tules.py Tules-instant.py Tules-sessions.py
```

### Issue: Python dependencies fail to install

**Cause:** pip is not installed or you don't have write permissions.

**Solution:**
```bash
# Ensure pip is installed
python3 -m ensurepip --upgrade

# Install with --user flag
pip install --user -r requirements.txt
```

### Issue: "Docker not found" warning

**Cause:** Docker is not installed.

**Impact:**
- Background agents (`Tules`/`T`) won't work
- Instant responses (`Tules-instant`/`Ti`) will still work
- Session management (`Tules-sessions`/`Ts`) will still work

**Solution (optional):**
Install Docker: https://docs.docker.com/get-docker/

### Issue: Remote install fails with "git not installed"

**Cause:** git is required for remote installation.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Or use Method 3 (manual installation)
```

### Issue: Symlinks point to wrong location

**Cause:** You moved the repository after installation.

**Solution:**
```bash
cd Tules
./install.sh  # Re-run installer to update symlinks
```

### Issue: Commands work during install but fail after terminal restart

**Cause:** This was a bug in older versions where remote installation deleted the cloned repository after creating symlinks, breaking the links.

**Solution:**
```bash
# Re-run the installer (this has been fixed)
curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash

# The new installer moves the repo to ~/.tules instead of deleting it
# Symlinks now point to the permanent location
```

## Uninstallation

To remove Tules:

```bash
cd Tules
./install.sh --uninstall
```

**Note:** For remote installations (via curl), the uninstaller removes both symlinks and the `~/.tules` directory. For local installations, only symlinks are removed.

**Complete removal (if needed):**

```bash
# If you cloned locally and want to remove everything
cd Tules
./install.sh --uninstall
cd ..
rm -rf Tules

# Remove background agent data (optional)
rm -rf ~/.claude/bg-agents
rm -rf ~/.gemini/bg-agents

# Remove remote installation directory (if installed via curl)
rm -rf ~/.tules
```

## Verification

After installation, verify everything works:

```bash
# Check if commands are available
Tules --help
Ti --help
Ts --help

# Test instant responses
Ti "what is 2+2?"

# List sessions (may be empty on first run)
Ts --list
```

## Post-Installation Setup

### First-time Docker setup

On first run, Tules will build Docker images:
- `tules-claude:latest` (for Claude Code)
- `tules-gemini:latest` (for Gemini CLI)

This is a one-time process that may take a few minutes.

### Choose Your Provider

Tules auto-detects available providers (Gemini first, then Claude). To explicitly set a provider:

```bash
# Use Claude
Ti --provider claude "your prompt"
Tules --provider claude run "your prompt"

# Use Gemini
Ti --provider gemini "your prompt"
Tules --provider gemini run "your prompt"
```

## Getting Help

- Documentation: See `CLAUDE.md` for architecture details
- Issues: Report at https://github.com/aymuos15/Tules/issues
- Run `--help` on any command for usage info
