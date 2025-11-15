#!/usr/bin/env python3
"""
claude-sessions - Session manager TUI for Claude Code
View and manage Claude Code sessions (folder-based).
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

console = Console()

# Session data class
class Session:
    def __init__(self, session_id: str, path: Path):
        self.id = session_id
        self.path = path
        self.is_agent = session_id.startswith('agent-')

        # Parse first line for metadata
        self.summary = 'No summary'
        self.cwd = None
        self.git_branch = None
        self.timestamp = datetime.fromtimestamp(path.stat().st_mtime)

        try:
            with open(path, 'r') as f:
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)
                    self.summary = data.get('summary', 'No summary')
                    self.cwd = data.get('cwd')
                    self.git_branch = data.get('gitBranch')
        except (json.JSONDecodeError, IOError):
            pass

    def get_full_conversation(self) -> List[Dict]:
        """Parse full conversation from JSONL"""
        messages = []
        try:
            with open(self.path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get('type') in ['user', 'assistant']:
                                messages.append(data)
                        except json.JSONDecodeError:
                            continue
        except IOError:
            pass
        return messages

    def __repr__(self):
        return f"Session({self.id[:8]}, {self.summary[:30]})"

def encode_directory(path: str) -> str:
    """Encode directory path for Claude storage (/ -> -)"""
    return path.replace('/', '-')

def decode_directory(encoded: str) -> str:
    """Decode directory path from Claude storage (- -> /)"""
    return encoded.replace('-', '/')

def find_sessions_for_directory(directory: str) -> List[Session]:
    """Find all sessions for a specific directory"""
    directory = os.path.abspath(directory)
    encoded_dir = encode_directory(directory)
    project_dir = Path.home() / '.claude' / 'projects' / encoded_dir

    if not project_dir.exists():
        return []

    sessions = []
    for jsonl_file in project_dir.glob('*.jsonl'):
        session_id = jsonl_file.stem
        sessions.append(Session(session_id, jsonl_file))

    # Sort by timestamp (newest first)
    return sorted(sessions, key=lambda s: s.timestamp, reverse=True)

def find_all_sessions() -> Dict[str, List[Session]]:
    """Find all sessions grouped by directory"""
    projects_dir = Path.home() / '.claude' / 'projects'

    if not projects_dir.exists():
        return {}

    sessions_by_dir = {}

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        decoded_dir = decode_directory(project_dir.name)
        sessions = find_sessions_for_directory(decoded_dir)

        if sessions:
            sessions_by_dir[decoded_dir] = sessions

    return sessions_by_dir

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

    # Build conversation text
    conversation = []
    for msg in messages[:20]:  # Limit to first 20 messages
        role = msg.get('message', {}).get('role', 'unknown')
        content = msg.get('message', {}).get('content', [])

        # Extract text content
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get('type') == 'text':
                text_parts.append(part.get('text', ''))

        if text_parts:
            text = '\n'.join(text_parts)
            conversation.append(f"[bold cyan]{role.upper()}:[/bold cyan]\n{text[:200]}{'...' if len(text) > 200 else ''}\n")

    detail_text = f"""[bold]Session ID:[/bold] {session.id}
[bold]Type:[/bold] {'Agent' if session.is_agent else 'Main Session'}
[bold]Summary:[/bold] {session.summary}
[bold]Working Directory:[/bold] {session.cwd or 'Unknown'}
[bold]Git Branch:[/bold] {session.git_branch or 'Unknown'}
[bold]Last Modified:[/bold] {session.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
[bold]Messages:[/bold] {len(messages)}

{'─' * 60}
[bold]Conversation Preview:[/bold]

{chr(10).join(conversation[:5])}

{'[dim]... showing first 5 messages[/dim]' if len(messages) > 5 else ''}
"""

    return Panel(
        detail_text,
        title=f"Session Details: {session.id[:8]}",
        border_style="cyan"
    )

def resume_session(session: Session, fork: bool = False):
    """Resume a session in the current terminal"""
    args = ['claude', '--resume', session.id]
    if fork:
        args.append('--fork-session')

    # Change to original working directory if available
    cwd = session.cwd if session.cwd and os.path.exists(session.cwd) else os.getcwd()

    console.print(f"\n[green]{'Forking' if fork else 'Resuming'} session {session.id[:8]}...[/green]\n")
    subprocess.run(args, cwd=cwd)

def interactive_session_browser(sessions: List[Session], directory: str):
    """Interactive TUI for browsing sessions"""
    if not sessions:
        console.print("[yellow]No sessions found for this directory[/yellow]")
        return

    selected_idx = 0
    view_mode = 'list'  # 'list' or 'detail'

    console.print("\n[bold cyan]Claude Code Session Browser[/bold cyan]")
    console.print("[dim]↑/↓: Navigate | Enter/v: View Details | r: Resume | f: Fork | q: Quit[/dim]\n")

    try:
        import sys
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
                console.print("[dim]↑/↓: Navigate | Enter/v: View Details | r: Resume | f: Fork | q: Quit[/dim]\n")
                table = create_session_table(sessions, directory, selected_idx)
                console.print(table)
            else:  # detail mode
                console.clear()
                console.print("\n[bold cyan]Session Details[/bold cyan]")
                console.print("[dim]b: Back to List | r: Resume | f: Fork | q: Quit[/dim]\n")
                panel = create_session_detail(sessions[selected_idx])
                console.print(panel)

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
                else:
                    view_mode = 'list'
            elif key == 'b' and view_mode == 'detail':
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
@click.option('--all', 'show_all', is_flag=True, help='Show sessions from all directories')
@click.option('--since', help='Filter sessions since date (YYYY-MM-DD)')
@click.option('--before', help='Filter sessions before date (YYYY-MM-DD)')
@click.option('--search', help='Search sessions by summary (regex)')
@click.option('--agents-only', is_flag=True, help='Show only agent sessions')
@click.option('--main-only', is_flag=True, help='Show only main sessions')
@click.option('--list', 'list_mode', is_flag=True, help='Non-interactive list mode')
def main(directory: Optional[str],
         show_all: bool,
         since: Optional[str],
         before: Optional[str],
         search: Optional[str],
         agents_only: bool,
         main_only: bool,
         list_mode: bool):
    """
    Claude Code Session Manager - View and manage sessions (folder-based)

    Examples:
        claude-sessions                  # Show sessions for current directory
        claude-sessions ~/my-project     # Show sessions for specific directory
        claude-sessions --all            # Show all sessions (grouped by directory)
        claude-sessions --since 2025-01-01 --search auth
    """

    if show_all:
        # Show all sessions grouped by directory
        all_sessions = find_all_sessions()

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

        sessions = find_sessions_for_directory(target_dir)

        # Apply filters
        sessions = filter_sessions(sessions, since, before, search, agents_only, main_only)

        if not sessions:
            console.print(f"[yellow]No sessions found for {target_dir}[/yellow]")
            console.print("[dim]Try running 'claude' in this directory first to create sessions[/dim]")
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
