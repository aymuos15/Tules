#!/usr/bin/env python3
"""
Tules - Background agent runner for Claude Code and Gemini CLI
Runs AI agents in headless sandboxed mode with no permission prompts.
Supports both Claude Code and Gemini CLI backends.
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
from tui_renderer import render_response

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.syntax import Syntax
import schedule
import time

# Import AI provider abstraction
from ai_provider import get_provider, detect_provider, get_all_providers

console = Console()

# Configuration - will be updated based on provider
BG_AGENTS_DIR = None
SESSIONS_FILE = None
LOGS_DIR = None
SCHEDULES_FILE = None

def init_config(provider_name: Optional[str] = None):
    """Initialize configuration based on provider"""
    global BG_AGENTS_DIR, SESSIONS_FILE, LOGS_DIR, SCHEDULES_FILE

    # Get provider
    if provider_name:
        provider = get_provider(provider_name)
        if not provider:
            console.print(f"[red]Unknown provider: {provider_name}[/red]")
            sys.exit(1)
        if not provider.is_available():
            console.print(f"[red]Provider '{provider_name}' is not available on this system[/red]")
            sys.exit(1)
    else:
        provider = detect_provider()
        if not provider:
            console.print("[red]No AI provider available. Please install claude or gemini-cli.[/red]")
            sys.exit(1)

    # Set paths based on provider
    BG_AGENTS_DIR = provider.get_bg_agents_dir()
    SESSIONS_FILE = BG_AGENTS_DIR / 'sessions.json'
    LOGS_DIR = BG_AGENTS_DIR / 'logs'
    SCHEDULES_FILE = BG_AGENTS_DIR / 'schedules.json'

    return provider

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

def check_git_repo() -> bool:
    """Check if current directory is a git repository"""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, check=True, cwd=os.getcwd())
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_current_branch() -> Optional[str]:
    """Get the current git branch name"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, check=True, cwd=os.getcwd())
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def sanitize_branch_name(prompt: str, session_id: str, provider_name: str = 'ai') -> str:
    """Generate a sanitized branch name from prompt and session ID"""
    # Take first 40 chars of prompt, remove special chars, convert to kebab-case
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9\s-]', '', prompt[:40])
    sanitized = re.sub(r'\s+', '-', sanitized).strip('-').lower()

    # Ensure it's not empty
    if not sanitized:
        sanitized = 'task'

    # Format: tules-<provider>/<prompt>-<short-session-id>
    short_id = session_id[:8]
    return f'tules-{provider_name}/{sanitized}-{short_id}'

def create_git_branch(branch_name: str) -> bool:
    """Create and checkout a new git branch"""
    try:
        # Create and checkout new branch
        subprocess.run(['git', 'checkout', '-b', branch_name], capture_output=True, check=True, cwd=os.getcwd())
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to create branch: {e.stderr.decode()}[/red]")
        return False

def check_docker() -> bool:
    """Check if Docker is available and running"""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_docker_image(provider_name: str = 'claude') -> bool:
    """Ensure Docker image is built for the given provider"""
    image_name = f'tules-{provider_name}:latest'

    # Check if image exists
    result = subprocess.run(
        ['docker', 'images', '-q', image_name],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        return True

    # Build image if it doesn't exist
    console.print(f"[yellow]Building {provider_name} Docker image (first time only)...[/yellow]")
    dockerfile_dir = Path(__file__).resolve().parent

    # Check if provider-specific Dockerfile exists
    dockerfile = dockerfile_dir / f'Dockerfile.{provider_name}'
    if not dockerfile.exists():
        # Fall back to generic Dockerfile
        dockerfile = dockerfile_dir / 'Dockerfile'

    if not dockerfile.exists():
        console.print(f"[red]Dockerfile not found at {dockerfile}[/red]")
        return False

    try:
        subprocess.run(
            ['docker', 'build', '-f', str(dockerfile), '-t', image_name, str(dockerfile_dir)],
            check=True,
            capture_output=True
        )
        console.print(f"[green]{provider_name} Docker image built successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to build Docker image: {e}[/red]")
        return False

def run_background(prompt: str, provider, session_id: Optional[str] = None, use_sandbox: bool = True) -> str:
    """
    Run AI agent in background with sandbox + skip-permissions

    Args:
        prompt: The prompt to run
        provider: AI provider instance
        session_id: Optional session ID (will generate if not provided)
        use_sandbox: Whether to use Docker sandboxing

    Returns:
        Session ID
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Check if we're in a git repo and create a branch
    branch_name = None
    original_branch = None
    if check_git_repo():
        original_branch = get_current_branch()
        branch_name = sanitize_branch_name(prompt, session_id, provider.get_name())

        if not create_git_branch(branch_name):
            console.print("[yellow]Warning: Failed to create branch, continuing without branch isolation[/yellow]")
            branch_name = None
    else:
        console.print("[yellow]Warning: Not a git repository, running without branch isolation[/yellow]")

    # Create log file
    log_path = LOGS_DIR / f'{session_id}.log'

    # Use Docker for sandboxing
    if use_sandbox:
        if not check_docker():
            console.print("[red]Error: Docker is not available. Please install Docker.[/red]")
            console.print("[yellow]Falling back to non-sandboxed execution[/yellow]")
            use_sandbox = False
        elif not ensure_docker_image(provider.get_name()):
            console.print("[yellow]Falling back to non-sandboxed execution[/yellow]")
            use_sandbox = False

    if use_sandbox:
        # Run in Docker container
        cwd = os.getcwd()
        home = str(Path.home())
        binary_path = provider.get_binary_path()

        # Docker command with volume mounts
        # Run as current user (not root) to allow skip-permissions
        uid = os.getuid()
        gid = os.getgid()

        container_name = f'tules-{provider.get_name()}-{session_id[:8]}'

        # Get provider-specific mounts
        mounts = provider.get_docker_mounts(cwd, home, binary_path)

        # Build docker command
        # For Gemini, use entrypoint to create user (fixes Node.js os.userInfo() error)
        # For Claude, use --user flag directly
        docker_cmd = [
            'docker', 'run',
            '--name', container_name,
            '--rm',  # Remove container when done
        ]

        if provider.get_name() == 'gemini':
            # Let entrypoint handle user creation
            docker_cmd += [
                '-e', f'USER_ID={uid}',
                '-e', f'GROUP_ID={gid}',
            ]
        else:
            # Claude: run as current user directly
            docker_cmd += ['--user', f'{uid}:{gid}']

        cmd = docker_cmd + mounts + [
            '-w', '/workspace',  # Set working directory
            '-e', f'SESSION_ID={session_id}',
            '-e', f'HOME={home}',  # Set HOME env var
            f'tules-{provider.get_name()}:latest',
        ] + provider.get_run_command(prompt, session_id, 'text')

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
        cmd = provider.get_run_command(prompt, session_id)

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=open(log_path, 'w'),
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
            start_new_session=True
        )

    # ...get AI response...
    ai_response = provider.run(prompt)
    
    # Render with TUI instead of plain print
    render_response(ai_response)
    
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
        'sandboxed': use_sandbox and check_docker(),
        'branch': branch_name,
        'original_branch': original_branch,
        'provider': provider.get_name()  # Store provider name
    })
    save_sessions(sessions)

    return ai_response, session_id

def get_session_status(session: Dict) -> str:
    """Check if session process is still running"""
    try:
        os.kill(session['pid'], 0)  # Signal 0 just checks if process exists
        return 'running'
    except OSError:
        return 'completed'

@click.group()
@click.option('--provider', type=click.Choice(['claude', 'gemini', 'auto'], case_sensitive=False),
              default='auto', help='AI provider to use (auto-detects if not specified)')
@click.pass_context
def cli(ctx, provider):
    """AI Background Agent Runner - Run agents in headless sandboxed mode

    Supports both Claude Code and Gemini CLI backends.

    \b
    Examples:
      Tules run "analyze this codebase for bugs"
      Tules --provider gemini run "explain this code"
      Tules list --all
      Tules logs a1b2c3d4
      Tules clear --force

    \b
    Each task runs in its own git branch (tules-<provider>/<task-description>-<id>)
    Use standard git commands to review and merge branches when complete.
    """
    # Initialize provider and store in context
    provider_name = None if provider == 'auto' else provider
    ctx.ensure_object(dict)
    ctx.obj['provider'] = init_config(provider_name)

@cli.command()
@click.argument('prompt')
@click.pass_context
def run(ctx, prompt: str):
    """Run a single task in background (always sandboxed)"""
    provider = ctx.obj['provider']
    ensure_dirs()

    session_id = run_background(prompt, provider, use_sandbox=True)

    # Get session info to display branch
    sessions = load_sessions()
    session = next((s for s in sessions if s['id'] == session_id), None)

    branch_info = ""
    if session and session.get('branch'):
        branch_info = f"Branch: [magenta]{session['branch']}[/magenta]\n"

    console.print(Panel(
        f"[green]Background agent started[/green]\n\n"
        f"Provider: [blue]{provider.get_name()}[/blue]\n"
        f"Session ID: [cyan]{session_id}[/cyan]\n"
        f"Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n"
        f"{branch_info}"
        f"Sandboxed: {'Yes (Docker)' if check_docker() else 'No (Docker not available)'}\n\n"
        f"View logs: [yellow]Tules logs {session_id[:8]}[/yellow]",
        title="🤖 Agent Started",
        border_style="green"
    ))

@cli.command()
@click.option('--all', 'show_all', is_flag=True, help='Show all sessions (including completed)')
@click.option('--provider-filter', type=str, help='Filter by provider (claude or gemini)')
def list(show_all: bool, provider_filter: Optional[str]):
    """List all background agents from all providers"""
    # Load sessions from all available providers
    all_sessions = []
    for provider in get_all_providers():
        if not provider.is_available():
            continue

        # Temporarily set config for this provider
        old_config = (BG_AGENTS_DIR, SESSIONS_FILE, LOGS_DIR, SCHEDULES_FILE)
        init_config(provider.get_name())

        provider_sessions = load_sessions()
        all_sessions.extend(provider_sessions)

        # Restore original config
        globals()['BG_AGENTS_DIR'], globals()['SESSIONS_FILE'], globals()['LOGS_DIR'], globals()['SCHEDULES_FILE'] = old_config

    sessions = all_sessions

    if not sessions:
        console.print("[yellow]No background agents found[/yellow]")
        return

    # Update statuses
    for session in sessions:
        session['status'] = get_session_status(session)

    # Apply provider filter if specified
    if provider_filter:
        sessions = [s for s in sessions if s.get('provider', 'claude') == provider_filter]

    # Filter by status if needed
    if not show_all:
        sessions = [s for s in sessions if s['status'] == 'running']

    if not sessions:
        console.print("[yellow]No running agents found (use --all to see completed)[/yellow]")
        return

    table = Table(title="Background Agents")
    table.add_column("Session ID", style="cyan")
    table.add_column("Provider", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Prompt", style="white")
    table.add_column("Branch", style="magenta")
    table.add_column("Started", style="yellow")
    table.add_column("Sandboxed", style="blue")

    for session in sessions:
        status_color = "green" if session['status'] == 'running' else "dim"
        branch_display = session.get('branch', 'N/A')
        if branch_display and branch_display != 'N/A':
            # Show just the last part after tules-<provider>/
            branch_display = branch_display.split('/')[-1][:20]

        table.add_row(
            session['id'][:8],
            session.get('provider', 'claude'),  # Default to claude for old sessions
            f"[{status_color}]{session['status']}[/{status_color}]",
            session['prompt'][:30],
            branch_display if branch_display else "N/A",
            datetime.fromisoformat(session['started']).strftime("%Y-%m-%d %H:%M"),
            "Yes" if session.get('sandboxed', False) else "No"
        )

    console.print(table)

@cli.command()
@click.argument('session_id')
@click.option('-f', '--follow', is_flag=True, help='Follow log output (like tail -f)')
@click.option('-n', '--lines', default=50, help='Number of lines to show (default: 50)')
def logs(session_id: str, follow: bool, lines: int):
    """View logs for a specific session from any provider"""
    # Load sessions from all available providers
    all_sessions = []
    for provider in get_all_providers():
        if not provider.is_available():
            continue

        # Temporarily set config for this provider
        old_config = (BG_AGENTS_DIR, SESSIONS_FILE, LOGS_DIR, SCHEDULES_FILE)
        init_config(provider.get_name())

        provider_sessions = load_sessions()
        all_sessions.extend(provider_sessions)

        # Restore original config
        globals()['BG_AGENTS_DIR'], globals()['SESSIONS_FILE'], globals()['LOGS_DIR'], globals()['SCHEDULES_FILE'] = old_config

    # Find matching session (allow partial ID)
    matching = [s for s in all_sessions if s['id'].startswith(session_id)]

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
@click.pass_context
def kill(ctx, session_id: str):
    """Stop a running agent"""
    provider = ctx.obj['provider']
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
        console.print(f"[green]Killed {provider.get_name()} session {session['id'][:8]}[/green]")

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
@click.pass_context
def schedule_task(ctx, cron_expr: str, prompt: str, name: Optional[str]):
    """Schedule a task (cron syntax: 'MIN HOUR DAY MONTH DAYOFWEEK')"""
    provider = ctx.obj['provider']
    schedules = load_schedules()

    schedule_id = str(uuid.uuid4())
    schedules.append({
        'id': schedule_id,
        'name': name or f'Task {len(schedules) + 1}',
        'cron': cron_expr,
        'prompt': prompt,
        'provider': provider.get_name(),
        'created': datetime.now().isoformat()
    })
    save_schedules(schedules)

    console.print(Panel(
        f"[green]Scheduled task created[/green]\n\n"
        f"Provider: [blue]{provider.get_name()}[/blue]\n"
        f"Name: {name or f'Task {len(schedules)}'}\n"
        f"Cron: {cron_expr}\n"
        f"Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n\n"
        f"[yellow]Run 'Tules daemon' to start the scheduler[/yellow]",
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
@click.pass_context
def clear(ctx, logs: bool, force: bool):
    """Clear all session history"""
    provider = ctx.obj['provider']
    sessions = load_sessions()

    if not sessions:
        console.print("[yellow]No sessions to clear[/yellow]")
        return

    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"Clear {len(sessions)} sessions for {provider.get_name()}?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Clear sessions
    save_sessions([])
    console.print(f"[green]Cleared {len(sessions)} {provider.get_name()} sessions[/green]")

    # Optionally clear log files
    if logs:
        import glob
        log_files = glob.glob(str(LOGS_DIR / '*.log'))
        for log_file in log_files:
            Path(log_file).unlink()
        console.print(f"[green]Deleted {len(log_files)} log files[/green]")

if __name__ == '__main__':
    cli()
