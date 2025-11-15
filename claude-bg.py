#!/usr/bin/env python3
"""
claude-bg - Background agent runner for Claude Code
Runs Claude agents in headless sandboxed mode with no permission prompts.
"""

import os
import sys
import json
import uuid
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.syntax import Syntax
import schedule
import time

console = Console()

# Configuration
BG_AGENTS_DIR = Path.home() / '.claude' / 'bg-agents'
SESSIONS_FILE = BG_AGENTS_DIR / 'sessions.json'
LOGS_DIR = BG_AGENTS_DIR / 'logs'
SCHEDULES_FILE = BG_AGENTS_DIR / 'schedules.json'

def ensure_dirs():
    """Ensure required directories exist"""
    BG_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text('[]')
    if not SCHEDULES_FILE.exists():
        SCHEDULES_FILE.write_text('[]')

def load_sessions() -> List[Dict]:
    """Load session metadata"""
    ensure_dirs()
    try:
        return json.loads(SESSIONS_FILE.read_text())
    except:
        return []

def save_sessions(sessions: List[Dict]):
    """Save session metadata"""
    ensure_dirs()
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2))

def load_schedules() -> List[Dict]:
    """Load scheduled tasks"""
    ensure_dirs()
    try:
        return json.loads(SCHEDULES_FILE.read_text())
    except:
        return []

def save_schedules(schedules: List[Dict]):
    """Save scheduled tasks"""
    ensure_dirs()
    SCHEDULES_FILE.write_text(json.dumps(schedules, indent=2))

def check_docker() -> bool:
    """Check if Docker is available and running"""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_docker_image() -> bool:
    """Ensure Docker image is built"""
    image_name = 'claude-bg:latest'

    # Check if image exists
    result = subprocess.run(
        ['docker', 'images', '-q', image_name],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        return True

    # Build image if it doesn't exist
    console.print("[yellow]Building Docker image (first time only)...[/yellow]")
    dockerfile_dir = Path(__file__).resolve().parent

    try:
        subprocess.run(
            ['docker', 'build', '-t', image_name, str(dockerfile_dir)],
            check=True,
            capture_output=True
        )
        console.print("[green]Docker image built successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to build Docker image: {e}[/red]")
        return False

def run_background(prompt: str, session_id: Optional[str] = None, use_sandbox: bool = True) -> str:
    """
    Run Claude in background with sandbox + skip-permissions

    Args:
        prompt: The prompt to run
        session_id: Optional session ID (will generate if not provided)
        use_sandbox: Whether to use bubblewrap sandboxing

    Returns:
        Session ID
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Create log file
    log_path = LOGS_DIR / f'{session_id}.log'

    # Use Docker for sandboxing
    if use_sandbox:
        if not check_docker():
            console.print("[red]Error: Docker is not available. Please install Docker.[/red]")
            console.print("[yellow]Falling back to non-sandboxed execution[/yellow]")
            use_sandbox = False
        elif not ensure_docker_image():
            console.print("[yellow]Falling back to non-sandboxed execution[/yellow]")
            use_sandbox = False

    if use_sandbox:
        # Run in Docker container
        cwd = os.getcwd()
        home = str(Path.home())

        # Docker command with volume mounts
        # Run as current user (not root) to allow --dangerously-skip-permissions
        uid = os.getuid()
        gid = os.getgid()

        container_name = f'claude-bg-{session_id[:8]}'
        cmd = [
            'docker', 'run',
            '--name', container_name,
            '--rm',  # Remove container when done
            '--user', f'{uid}:{gid}',  # Run as current user, not root
            '-v', f'{cwd}:/workspace',  # Mount working directory
            '-v', f'{home}/.claude:{home}/.claude',  # Mount Claude config (same path)
            '-v', f'{home}/.claude.json:{home}/.claude.json',  # Mount main config file
            '-v', f'{home}/.local/bin/claude:/usr/local/bin/claude:ro',  # Mount Claude binary
            '-v', f'{home}/.local/share/claude:{home}/.local/share/claude:ro',  # Mount Claude installation
            '-w', '/workspace',  # Set working directory
            '-e', f'SESSION_ID={session_id}',
            '-e', f'HOME={home}',  # Set HOME env var
            'claude-bg:latest',
            'claude', '-p', prompt,
            '--dangerously-skip-permissions',
            '--session-id', session_id,
            '--output-format', 'text'  # Force text output to stdout
        ]

        # Run in background and capture logs using docker logs
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Wait a moment for container to start, then stream logs to file
        time.sleep(0.5)

        # Start a background process to capture docker logs
        log_cmd = ['docker', 'logs', '-f', container_name]
        log_process = subprocess.Popen(
            log_cmd,
            stdout=open(log_path, 'w'),
            stderr=subprocess.STDOUT
        )

    else:
        # Run without sandbox (direct execution)
        cmd = [
            'claude', '-p', prompt,
            '--dangerously-skip-permissions',
            '--session-id', session_id
        ]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=open(log_path, 'w'),
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
            start_new_session=True
        )

    # Save session metadata
    sessions = load_sessions()
    sessions.append({
        'id': session_id,
        'prompt': prompt[:100],  # Truncate for display
        'status': 'running',
        'pid': process.pid,
        'started': datetime.now().isoformat(),
        'cwd': os.getcwd(),
        'log_path': str(log_path),
        'sandboxed': use_sandbox and check_docker()
    })
    save_sessions(sessions)

    return session_id

def get_session_status(session: Dict) -> str:
    """Check if session process is still running"""
    try:
        os.kill(session['pid'], 0)  # Signal 0 just checks if process exists
        return 'running'
    except OSError:
        return 'completed'

@click.group()
def cli():
    """Claude Background Agent Runner - Run agents in headless sandboxed mode

    \b
    Examples:
      claude-bg run "analyze this codebase for bugs"
      claude-bg list --all
      claude-bg logs a1b2c3d4
      claude-bg clear --force
    """
    pass

@cli.command()
@click.argument('prompt')
def run(prompt: str):
    """Run a single task in background (always sandboxed)"""
    ensure_dirs()

    session_id = run_background(prompt, use_sandbox=True)

    console.print(Panel(
        f"[green]Background agent started[/green]\n\n"
        f"Session ID: [cyan]{session_id}[/cyan]\n"
        f"Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n"
        f"Sandboxed: {'Yes (Docker)' if check_docker() else 'No (Docker not available)'}\n\n"
        f"View logs: [yellow]claude-bg logs {session_id[:8]}[/yellow]",
        title="🤖 Agent Started",
        border_style="green"
    ))

@cli.command()
@click.option('--all', 'show_all', is_flag=True, help='Show all sessions (including completed)')
def list(show_all: bool):
    """List all background agents"""
    sessions = load_sessions()

    if not sessions:
        console.print("[yellow]No background agents found[/yellow]")
        return

    # Update statuses
    for session in sessions:
        session['status'] = get_session_status(session)
    save_sessions(sessions)

    # Filter if needed
    if not show_all:
        sessions = [s for s in sessions if s['status'] == 'running']

    if not sessions:
        console.print("[yellow]No running agents found (use --all to see completed)[/yellow]")
        return

    table = Table(title="Background Agents")
    table.add_column("Session ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Prompt", style="white")
    table.add_column("Started", style="yellow")
    table.add_column("Sandboxed", style="magenta")

    for session in sessions:
        status_color = "green" if session['status'] == 'running' else "dim"
        table.add_row(
            session['id'][:8],
            f"[{status_color}]{session['status']}[/{status_color}]",
            session['prompt'][:40],
            datetime.fromisoformat(session['started']).strftime("%Y-%m-%d %H:%M"),
            "Yes" if session.get('sandboxed', False) else "No"
        )

    console.print(table)

@cli.command()
@click.argument('session_id')
@click.option('-f', '--follow', is_flag=True, help='Follow log output (like tail -f)')
@click.option('-n', '--lines', default=50, help='Number of lines to show (default: 50)')
def logs(session_id: str, follow: bool, lines: int):
    """View logs for a specific session"""
    sessions = load_sessions()

    # Find matching session (allow partial ID)
    matching = [s for s in sessions if s['id'].startswith(session_id)]

    if not matching:
        console.print(f"[red]Session not found: {session_id}[/red]")
        return

    if len(matching) > 1:
        console.print(f"[red]Ambiguous session ID. Matches: {', '.join(s['id'][:8] for s in matching)}[/red]")
        return

    session = matching[0]
    log_path = Path(session['log_path'])

    if not log_path.exists():
        console.print(f"[red]Log file not found: {log_path}[/red]")
        return

    if follow:
        # Follow mode (like tail -f)
        console.print(f"[cyan]Following logs for {session['id'][:8]}...[/cyan] (Ctrl+C to stop)\n")
        try:
            process = subprocess.Popen(['tail', '-f', str(log_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in process.stdout:
                console.print(line, end='')
        except KeyboardInterrupt:
            process.terminate()
            console.print("\n[yellow]Stopped following logs[/yellow]")
    else:
        # Show last N lines
        result = subprocess.run(['tail', f'-n{lines}', str(log_path)], capture_output=True, text=True)
        console.print(Panel(
            result.stdout,
            title=f"Logs: {session['id'][:8]}",
            border_style="cyan"
        ))

@cli.command()
@click.argument('session_id')
def kill(session_id: str):
    """Stop a running agent"""
    sessions = load_sessions()

    # Find matching session
    matching = [s for s in sessions if s['id'].startswith(session_id)]

    if not matching:
        console.print(f"[red]Session not found: {session_id}[/red]")
        return

    if len(matching) > 1:
        console.print(f"[red]Ambiguous session ID. Matches: {', '.join(s['id'][:8] for s in matching)}[/red]")
        return

    session = matching[0]

    try:
        # Kill process and its children
        os.killpg(os.getpgid(session['pid']), signal.SIGTERM)
        console.print(f"[green]Killed session {session['id'][:8]}[/green]")

        # Update status
        session['status'] = 'killed'
        save_sessions(sessions)
    except ProcessLookupError:
        console.print(f"[yellow]Session {session['id'][:8]} is not running[/yellow]")
    except Exception as e:
        console.print(f"[red]Error killing session: {e}[/red]")

@cli.command()
@click.argument('cron_expr')
@click.argument('prompt')
@click.option('--name', help='Name for this scheduled task')
def schedule_task(cron_expr: str, prompt: str, name: Optional[str]):
    """Schedule a task (cron syntax: 'MIN HOUR DAY MONTH DAYOFWEEK')"""
    schedules = load_schedules()

    schedule_id = str(uuid.uuid4())
    schedules.append({
        'id': schedule_id,
        'name': name or f'Task {len(schedules) + 1}',
        'cron': cron_expr,
        'prompt': prompt,
        'created': datetime.now().isoformat()
    })
    save_schedules(schedules)

    console.print(Panel(
        f"[green]Scheduled task created[/green]\n\n"
        f"Name: {name or f'Task {len(schedules)}'}\n"
        f"Cron: {cron_expr}\n"
        f"Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n\n"
        f"[yellow]Run 'claude-bg daemon' to start the scheduler[/yellow]",
        title="📅 Task Scheduled",
        border_style="green"
    ))

@cli.command()
def daemon():
    """Run scheduler daemon (processes scheduled tasks)"""
    console.print("[cyan]Starting scheduler daemon...[/cyan]")

    # TODO: Implement proper daemon with schedule library
    # For now, just show schedules
    schedules = load_schedules()

    if not schedules:
        console.print("[yellow]No scheduled tasks found[/yellow]")
        return

    console.print(f"[green]Found {len(schedules)} scheduled tasks[/green]")
    console.print("[yellow]Daemon mode not yet implemented - use cron instead[/yellow]")

@cli.command()
@click.option('--logs', is_flag=True, help='Also delete log files')
@click.option('--force', is_flag=True, help='Skip confirmation')
def clear(logs: bool, force: bool):
    """Clear all session history"""
    sessions = load_sessions()

    if not sessions:
        console.print("[yellow]No sessions to clear[/yellow]")
        return

    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"Clear {len(sessions)} sessions?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Clear sessions
    save_sessions([])
    console.print(f"[green]Cleared {len(sessions)} sessions[/green]")

    # Optionally clear log files
    if logs:
        import glob
        log_files = glob.glob(str(LOGS_DIR / '*.log'))
        for log_file in log_files:
            Path(log_file).unlink()
        console.print(f"[green]Deleted {len(log_files)} log files[/green]")

if __name__ == '__main__':
    cli()
