#!/usr/bin/env bash
#
# Tules Installation Script
# Installs Tules background agent runner for Claude Code and Gemini CLI
#
# Usage:
#   ./install.sh              # Install (local)
#   curl -sSL https://raw.githubusercontent.com/aymuos15/Tules/master/install.sh | bash  # Remote install
#   ./install.sh --uninstall  # Uninstall
#
# NOTE: Remote installation (via curl) only works for PUBLIC repositories.
# For PRIVATE repositories, clone first then run ./install.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="$HOME/.local/bin"
PERMANENT_DIR="$HOME/.tules"  # Permanent location for cloned repo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Repository info for remote installation
REPO_URL="https://github.com/aymuos15/Tules.git"
REPO_BRANCH="master"
CLONE_DIR="$HOME/.tules-install-temp"

# Files to symlink
SYMLINKS=(
    "Tules.py:Tules"
    "Tules.py:T"
    "Tules-sessions.py:Tules-sessions"
    "Tules-sessions.py:Ts"
    "Tules-instant.py:Tules-instant"
    "Tules-instant.py:Ti"
)

#------------------------------------------------------------------------------
# Helper Functions
#------------------------------------------------------------------------------

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_python_version() {
    if ! check_command python3; then
        print_error "Python 3 is not installed"
        print_info "Please install Python 3.8 or higher"
        exit 1
    fi

    local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 8 ]; }; then
        print_error "Python 3.8+ required, found $version"
        exit 1
    fi

    print_success "Python $version detected"
}

check_pip() {
    if ! check_command pip3 && ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not installed"
        print_info "Please install pip: python3 -m ensurepip --upgrade"
        exit 1
    fi
    print_success "pip detected"
}

check_docker() {
    if check_command docker; then
        print_success "Docker detected (recommended for sandboxing)"
    else
        print_warning "Docker not found - Docker is recommended but not required"
        print_info "Install Docker from: https://docs.docker.com/get-docker/"
    fi
}

check_git() {
    if ! check_command git; then
        print_error "git is not installed"
        print_info "Please install git to clone the repository"
        exit 1
    fi
    print_success "git detected"
}

is_remote_install() {
    # Check if we're being piped from curl (no tty, and script files don't exist)
    if [ ! -t 0 ] && [ ! -f "$SCRIPT_DIR/Tules.py" ]; then
        return 0
    fi
    return 1
}

clone_repository() {
    print_info "Cloning Tules repository..."

    # Remove old clone directory if it exists
    if [ -d "$CLONE_DIR" ]; then
        rm -rf "$CLONE_DIR"
    fi

    # Clone the repository
    git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$CLONE_DIR" 2>&1 | grep -v "Cloning into" || true

    if [ ! -d "$CLONE_DIR" ]; then
        print_error "Failed to clone repository"
        exit 1
    fi

    # Update SCRIPT_DIR to point to cloned repo
    SCRIPT_DIR="$CLONE_DIR"
    print_success "Repository cloned to $CLONE_DIR"
}

move_to_permanent_location() {
    print_info "Moving installation to permanent location..."

    # Remove old permanent directory if it exists
    if [ -d "$PERMANENT_DIR" ]; then
        rm -rf "$PERMANENT_DIR"
    fi

    # Move clone to permanent location
    mv "$CLONE_DIR" "$PERMANENT_DIR"

    # Update SCRIPT_DIR to permanent location
    SCRIPT_DIR="$PERMANENT_DIR"

    print_success "Installed to $PERMANENT_DIR"
}

install_dependencies() {
    print_info "Installing Python dependencies..."

    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        python3 -m pip install --user -r "$SCRIPT_DIR/requirements.txt" --quiet
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found in $SCRIPT_DIR"
        exit 1
    fi
}

create_install_dir() {
    if [ ! -d "$INSTALL_DIR" ]; then
        print_info "Creating $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR"
        print_success "Created $INSTALL_DIR"
    fi
}

create_symlinks() {
    print_info "Creating symlinks in $INSTALL_DIR..."

    local failed=0
    for link_spec in "${SYMLINKS[@]}"; do
        local source_file="${link_spec%%:*}"
        local link_name="${link_spec##*:}"
        local source_path="$SCRIPT_DIR/$source_file"
        local link_path="$INSTALL_DIR/$link_name"

        # Check if source exists
        if [ ! -f "$source_path" ]; then
            print_error "Source file not found: $source_path"
            failed=1
            continue
        fi

        # Make source executable
        chmod +x "$source_path"

        # Remove existing symlink if it exists
        if [ -L "$link_path" ]; then
            rm "$link_path"
        elif [ -e "$link_path" ]; then
            print_warning "File exists (not a symlink): $link_path - skipping"
            continue
        fi

        # Create symlink
        ln -s "$source_path" "$link_path"
        print_success "Created symlink: $link_name -> $source_file"
    done

    if [ $failed -eq 1 ]; then
        print_error "Some symlinks failed to create"
        exit 1
    fi
}

remove_symlinks() {
    print_info "Removing symlinks from $INSTALL_DIR..."

    for link_spec in "${SYMLINKS[@]}"; do
        local link_name="${link_spec##*:}"
        local link_path="$INSTALL_DIR/$link_name"

        if [ -L "$link_path" ]; then
            rm "$link_path"
            print_success "Removed symlink: $link_name"
        elif [ -e "$link_path" ]; then
            print_warning "Not a symlink (skipping): $link_path"
        fi
    done
}

check_path() {
    if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        print_success "$INSTALL_DIR is in your PATH"
        return 0
    else
        print_warning "$INSTALL_DIR is NOT in your PATH"
        return 1
    fi
}

add_to_path() {
    local shell_rc=""

    # Detect shell config file
    if [ -n "$BASH_VERSION" ]; then
        if [ -f "$HOME/.bashrc" ]; then
            shell_rc="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            shell_rc="$HOME/.bash_profile"
        fi
    elif [ -n "$ZSH_VERSION" ]; then
        shell_rc="$HOME/.zshrc"
    else
        # Try to detect from SHELL variable
        case "$SHELL" in
            */bash)
                shell_rc="$HOME/.bashrc"
                [ -f "$HOME/.bash_profile" ] && shell_rc="$HOME/.bash_profile"
                ;;
            */zsh)
                shell_rc="$HOME/.zshrc"
                ;;
            *)
                print_warning "Could not detect shell type"
                ;;
        esac
    fi

    if [ -z "$shell_rc" ]; then
        print_warning "Could not determine shell configuration file"
        print_info "Please add this line to your shell config manually:"
        echo ""
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        return
    fi

    print_info "Would you like to add $INSTALL_DIR to your PATH?"
    echo -n "This will modify $shell_rc [y/N]: "
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "" >> "$shell_rc"
        echo "# Added by Tules installer" >> "$shell_rc"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$shell_rc"
        print_success "Added to $shell_rc"
        print_info "Run 'source $shell_rc' or restart your terminal to apply changes"
    else
        print_info "Skipped. You can add it manually:"
        echo ""
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
    fi
}

verify_installation() {
    print_info "Verifying installation..."

    local all_ok=true

    for link_spec in "${SYMLINKS[@]}"; do
        local link_name="${link_spec##*:}"

        if check_command "$link_name"; then
            print_success "$link_name is available"
        else
            print_error "$link_name is NOT available in PATH"
            all_ok=false
        fi
    done

    if [ "$all_ok" = true ]; then
        echo ""
        print_success "Installation complete!"
        echo ""
        echo "Try running:"
        echo "  Tules --help"
        echo "  Ti 'what is 2+2?'"
        echo "  Ts --list"
        echo ""
    else
        echo ""
        print_warning "Installation completed with warnings"
        print_info "Make sure $INSTALL_DIR is in your PATH"
        echo ""
    fi
}

#------------------------------------------------------------------------------
# Main Installation
#------------------------------------------------------------------------------

install() {
    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   Tules Installation Script           ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""

    # Detect if this is a remote installation
    local is_remote=false
    if is_remote_install; then
        is_remote=true
        print_info "Detected remote installation (via curl)"
    else
        print_info "Detected local installation"
    fi

    print_info "Checking system requirements..."
    check_python_version
    check_pip
    check_docker

    # Clone repository if remote install
    if [ "$is_remote" = true ]; then
        echo ""
        check_git
        clone_repository
        echo ""
        move_to_permanent_location
    fi

    echo ""
    install_dependencies

    echo ""
    create_install_dir
    create_symlinks

    echo ""
    if ! check_path; then
        add_to_path
    fi

    echo ""
    verify_installation
}

#------------------------------------------------------------------------------
# Uninstall
#------------------------------------------------------------------------------

uninstall() {
    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   Tules Uninstaller                   ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""

    print_warning "This will remove Tules symlinks from $INSTALL_DIR"
    if [ -d "$PERMANENT_DIR" ]; then
        print_warning "This will also remove the installation directory: $PERMANENT_DIR"
    fi
    echo -n "Continue? [y/N]: "
    read -r response

    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_info "Uninstall cancelled"
        exit 0
    fi

    echo ""
    remove_symlinks

    # Remove permanent directory if it exists
    if [ -d "$PERMANENT_DIR" ]; then
        echo ""
        print_info "Removing installation directory..."
        rm -rf "$PERMANENT_DIR"
        print_success "Removed $PERMANENT_DIR"
    fi

    echo ""
    print_success "Uninstall complete"
    print_info "Note: Python dependencies and config files (~/.claude, ~/.gemini) were not removed"
    echo ""
}

#------------------------------------------------------------------------------
# Entry Point
#------------------------------------------------------------------------------

if [ "$1" = "--uninstall" ]; then
    uninstall
else
    install
fi
