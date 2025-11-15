#!/usr/bin/env python3
"""
Tules-sessions - Session manager TUI for Claude Code and Gemini CLI
View and manage AI sessions (folder-based).
Supports both Claude Code and Gemini CLI backends.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live

# Import AI provider abstraction
from ai_provider import get_provider, detect_provider, get_all_providers

console = Console()

# Session data class
class Session:
    def __init__(self, session_path: Path, provider):
        """Initialize session from file using provider abstraction"""
        self.path = session_path
        self.provider = provider

        # Parse metadata using provider
        metadata = provider.parse_session_file(session_path)

        self.id = metadata['id']
        self.summary = metadata['summary']
        self.cwd = metadata.get('cwd')
        self.git_branch = metadata.get('git_branch')
        self.timestamp = metadata['timestamp']
        self.is_agent = metadata.get('is_agent', False)
        self.messages = metadata.get('messages', [])

    def get_full_conversation(self) -> List[Dict]:
        """Get full conversation messages"""
        return self.messages

    def get_log_path(self) -> Optional[Path]:
        """Get log file path for background agent sessions"""
        if not self.id:
            return None

        # Get provider's bg-agents directory
        bg_agents_dir = self.provider.get_bg_agents_dir()
        logs_dir = bg_agents_dir / 'logs'

        # Log file is named {session_id}.log
        log_file = logs_dir / f'{self.id}.log'

        return log_file if log_file.exists() else None

    def __repr__(self):
        return f"Session({self.id[:8] if self.id else 'unknown'}, {self.summary[:30]})"

def find_sessions_for_directory(directory: str, provider) -> List[Session]:
    """Find all sessions for a specific directory using provider abstraction"""
    directory = os.path.abspath(directory)

    # Get session files using provider
    session_files = provider.find_session_files(directory)

    if not session_files:
        return []

    sessions = []
    for session_file in session_files:
        try:
            session = Session(session_file, provider)
            sessions.append(session)
        except Exception as e:
            # Skip files that can't be parsed
            console.print(f"[dim]Warning: Could not parse {session_file.name}: {e}[/dim]")
            continue

    # Sort by timestamp (newest first)
    return sorted(sessions, key=lambda s: s.timestamp, reverse=True)

def find_all_sessions(provider) -> Dict[str, List[Session]]:
    """Find all sessions grouped by directory"""
    # For now, this is complex to implement generically
    # We would need to scan all possible project directories
    # Let's simplify and just return sessions for current dir
    # Users can use --all with a specific provider
    console.print("[yellow]Note: --all flag with multi-provider is not yet fully supported[/yellow]")
    console.print("[yellow]Showing sessions for current directory only[/yellow]")

    cwd = os.getcwd()
    sessions = find_sessions_for_directory(cwd, provider)

    if sessions:
        return {cwd: sessions}
    return {}

def filter_sessions(sessions: List[Session],
                   since: Optional[str] = None,
                   before: Optional[str] = None,
                   search: Optional[str] = None,
                   agents_only: bool = False,
                   main_only: bool = False) -> List[Session]:
    """Filter sessions based on criteria"""

    filtered = sessions

    # Date filters
    if since:
        since_date = datetime.fromisoformat(since)
        filtered = [s for s in filtered if s.timestamp >= since_date]

    if before:
        before_date = datetime.fromisoformat(before)
        filtered = [s for s in filtered if s.timestamp <= before_date]

    # Search filter
    if search:
        pattern = re.compile(search, re.IGNORECASE)
        filtered = [s for s in filtered if pattern.search(s.summary)]

    # Type filters
    if agents_only:
        filtered = [s for s in filtered if s.is_agent]
    elif main_only:
        filtered = [s for s in filtered if not s.is_agent]

    return filtered

def create_session_table(sessions: List[Session], directory: str, selected_idx: int = -1) -> Table:
    """Create a Rich table for session list"""
    table = Table(title=f"📁 Sessions for {directory}", title_style="bold cyan")
    table.add_column("", width=2)  # Selection indicator
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Type", style="magenta", width=8)
    table.add_column("Summary", style="white")
    table.add_column("Date", style="yellow", width=16)

    for i, session in enumerate(sessions):
        prefix = ">" if i == selected_idx else " "
        style = "bold green" if i == selected_idx else ""

        session_type = "[magenta]AGENT[/magenta]" if session.is_agent else "[blue]MAIN[/blue]"

        table.add_row(
            prefix,
            session.id[:8],
            session_type,
            session.summary[:60],
            session.timestamp.strftime("%Y-%m-%d %H:%M"),
            style=style
        )

    return table

def create_session_detail(session: Session) -> Panel:
    """Create a Rich panel for session details"""
    messages = session.get_full_conversation()

    # Build conversation text - show ALL messages with more content
    conversation = []
    for idx, msg in enumerate(messages):
        role = msg.get('message', {}).get('role', 'unknown')
        content = msg.get('message', {}).get('content', [])

        # Extract text content
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get('type') == 'text':
                text_parts.append(part.get('text', ''))

        if text_parts:
            text = '\n'.join(text_parts)
            # Show first 1000 chars instead of 200, add message number
            truncated = text[:1000]
            if len(text) > 1000:
                truncated += f"\n[dim]... (truncated, {len(text)} chars total)[/dim]"
            conversation.append(f"[bold cyan]Message {idx + 1} - {role.upper()}:[/bold cyan]\n{truncated}\n")

    detail_text = f"""[bold]Session ID:[/bold] {session.id}
[bold]Type:[/bold] {'Agent' if session.is_agent else 'Main Session'}
[bold]Summary:[/bold] {session.summary}
[bold]Working Directory:[/bold] {session.cwd or 'Unknown'}
[bold]Git Branch:[/bold] {session.git_branch or 'Unknown'}
[bold]Last Modified:[/bold] {session.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
[bold]Total Messages:[/bold] {len(messages)}

{'─' * 80}
[bold]Full Conversation:[/bold]

{chr(10).join(conversation)}
"""

    return Panel(
        detail_text,
        title=f"Session Details: {session.id[:8]} ({len(messages)} messages)",
        border_style="cyan"
    )

def create_log_popup(session: Session, lines: int = 100) -> Optional[Panel]:
    """Create a centered popup panel for displaying logs"""
    log_path = session.get_log_path()

    if not log_path:
        return Panel(
            "[yellow]No log file found for this session.[/yellow]\n\n"
            "[dim]Note: Only background agent sessions have log files.[/dim]",
            title=f"Logs: {session.id[:8] if session.id else 'unknown'}",
            border_style="yellow"
        )

    try:
        # Read last N lines of log file
        result = subprocess.run(
            ['tail', f'-n{lines}', str(log_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return Panel(
                f"[red]Error reading log file:[/red]\n{result.stderr}",
                title=f"Logs: {session.id[:8] if session.id else 'unknown'}",
                border_style="red"
            )

        log_content = result.stdout if result.stdout else "[dim]Log file is empty[/dim]"

        return Panel(
            log_content,
            title=f"Logs: {session.id[:8] if session.id else 'unknown'} (last {lines} lines)",
            border_style="green",
            subtitle="[dim]Press 'b' to go back[/dim]"
        )

    except Exception as e:
        return Panel(
            f"[red]Error reading log file:[/red]\n{str(e)}",
            title=f"Logs: {session.id[:8] if session.id else 'unknown'}",
            border_style="red"
        )

def resume_session(session: Session, fork: bool = False):
    """Resume a session in the current terminal"""
    # Get resume command from provider
    args = session.provider.get_resume_command(session.id, fork)

    if args is None:
        console.print(f"[red]Session forking is not supported by {session.provider.get_name()}[/red]")
        return

    # Change to original working directory if available
    cwd = session.cwd if session.cwd and os.path.exists(session.cwd) else os.getcwd()

    console.print(f"\n[green]{'Forking' if fork else 'Resuming'} session {session.id[:8] if session.id else 'unknown'}...[/green]\n")
    subprocess.run(args, cwd=cwd)

def interactive_session_browser(sessions: List[Session], directory: str):
    """Interactive TUI for browsing sessions"""
    if not sessions:
        console.print("[yellow]No sessions found for this directory[/yellow]")
        return

    # Check if stdin is a TTY (required for interactive mode)
    import sys
    if not sys.stdin.isatty():
        console.print("[yellow]Interactive mode requires a TTY (terminal)[/yellow]")
        console.print("[yellow]Use --list for non-interactive mode, or run directly in a terminal[/yellow]")
        # Fall back to static list
        table = create_session_table(sessions, directory)
        console.print(table)
        return

    selected_idx = 0
    view_mode = 'list'  # 'list', 'detail', or 'logs'

    console.print("\n[bold cyan]Claude Code Session Browser[/bold cyan]")
    console.print("[dim]↑/↓: Navigate | Enter/v: View Details | l: View Logs | r: Resume | f: Fork | q: Quit[/dim]\n")

    try:
        import tty
        import termios

        def get_key():
            """Get a single keypress"""
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                # Handle arrow keys (escape sequences)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A':
                            return 'up'
                        elif ch3 == 'B':
                            return 'down'
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        while True:
            # Clear screen and show content
            if view_mode == 'list':
                console.clear()
                console.print("\n[bold cyan]Claude Code Session Browser[/bold cyan]")
                console.print("[dim]↑/↓: Navigate | Enter/v: View Details | l: View Logs | r: Resume | f: Fork | q: Quit[/dim]\n")
                table = create_session_table(sessions, directory, selected_idx)
                console.print(table)
            elif view_mode == 'detail':
                console.clear()
                console.print("\n[bold cyan]Session Details[/bold cyan]")
                console.print("[dim]b: Back to List | l: View Logs | r: Resume | f: Fork | q: Quit[/dim]\n")
                panel = create_session_detail(sessions[selected_idx])
                console.print(panel)
            elif view_mode == 'logs':
                console.clear()
                console.print("\n[bold cyan]Session Logs[/bold cyan]")
                console.print("[dim]b: Back to List | q: Quit[/dim]\n")
                log_panel = create_log_popup(sessions[selected_idx])
                console.print(log_panel)

            # Get input
            key = get_key()

            if key == 'q':
                break
            elif key == 'up' and view_mode == 'list':
                selected_idx = max(0, selected_idx - 1)
            elif key == 'down' and view_mode == 'list':
                selected_idx = min(len(sessions) - 1, selected_idx + 1)
            elif key in ['\r', '\n', 'v']:  # Enter or 'v'
                if view_mode == 'list':
                    view_mode = 'detail'
                elif view_mode in ['detail', 'logs']:
                    view_mode = 'list'
            elif key == 'l':  # View logs
                view_mode = 'logs'
            elif key == 'b' and view_mode in ['detail', 'logs']:
                view_mode = 'list'
            elif key == 'r':
                resume_session(sessions[selected_idx], fork=False)
                break
            elif key == 'f':
                resume_session(sessions[selected_idx], fork=True)
                break

    except ImportError:
        # Fallback: non-interactive mode
        console.print("[yellow]Interactive mode not available (termios not found)[/yellow]")
        console.print("[yellow]Use --list to view sessions non-interactively[/yellow]")

@click.command()
@click.argument('directory', default=None, required=False)
@click.option('--provider', type=click.Choice(['claude', 'gemini', 'auto'], case_sensitive=False),
              default='auto', help='AI provider to use (auto-detects if not specified)')
@click.option('--all', 'show_all', is_flag=True, help='Show sessions from all directories')
@click.option('--since', help='Filter sessions since date (YYYY-MM-DD)')
@click.option('--before', help='Filter sessions before date (YYYY-MM-DD)')
@click.option('--search', help='Search sessions by summary (regex)')
@click.option('--agents-only', is_flag=True, help='Show only agent sessions')
@click.option('--main-only', is_flag=True, help='Show only main sessions')
@click.option('--list', 'list_mode', is_flag=True, help='Non-interactive list mode')
def main(directory: Optional[str],
         provider: str,
         show_all: bool,
         since: Optional[str],
         before: Optional[str],
         search: Optional[str],
         agents_only: bool,
         main_only: bool,
         list_mode: bool):
    """
    AI Session Manager - View and manage sessions (folder-based)

    Supports both Claude Code and Gemini CLI backends.

    Examples:
        Tules-sessions                      # Show sessions for current directory
        Tules-sessions --provider gemini    # Show Gemini sessions
        Tules-sessions ~/my-project         # Show sessions for specific directory
        Tules-sessions --all                # Show all sessions (grouped by directory)
        Tules-sessions --since 2025-01-01 --search auth
    """

    # Get provider
    provider_name = None if provider == 'auto' else provider
    if provider_name:
        ai_provider = get_provider(provider_name)
        if not ai_provider:
            console.print(f"[red]Unknown provider: {provider_name}[/red]")
            return
        if not ai_provider.is_available():
            console.print(f"[red]Provider '{provider_name}' is not available on this system[/red]")
            return
    else:
        ai_provider = detect_provider()
        if not ai_provider:
            console.print("[red]No AI provider available. Please install claude or gemini-cli.[/red]")
            return

    console.print(f"[dim]Using provider: {ai_provider.get_name()}[/dim]\n")

    if show_all:
        # Show all sessions grouped by directory
        all_sessions = find_all_sessions(ai_provider)

        if not all_sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return

        for dir_path, sessions in all_sessions.items():
            # Apply filters
            filtered = filter_sessions(sessions, since, before, search, agents_only, main_only)

            if filtered:
                table = create_session_table(filtered, dir_path)
                console.print(table)
                console.print()

    else:
        # Show sessions for specific directory
        target_dir = directory if directory else os.getcwd()
        target_dir = os.path.abspath(target_dir)

        sessions = find_sessions_for_directory(target_dir, ai_provider)

        # Apply filters
        sessions = filter_sessions(sessions, since, before, search, agents_only, main_only)

        if not sessions:
            console.print(f"[yellow]No sessions found for {target_dir}[/yellow]")
            console.print(f"[dim]Try running '{ai_provider.get_name()}' in this directory first to create sessions[/dim]")
            return

        if list_mode:
            # Non-interactive list mode
            table = create_session_table(sessions, target_dir)
            console.print(table)
        else:
            # Interactive TUI mode
            interactive_session_browser(sessions, target_dir)

if __name__ == '__main__':
    main()
