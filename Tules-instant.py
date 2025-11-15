#!/usr/bin/env python3
"""
Tules-instant - Instant AI CLI with rich rendering

Quick interactive AI responses using CLI commands (not background agents).
Supports both Gemini and Claude with automatic provider detection.
"""

import sys
import subprocess
import click
from rich.console import Console

from tui_renderer import render_response
from ai_provider import detect_provider

console = Console()

TULES_ASCII = r"""
 _____ _   _ _     _____ ____
|_   _| | | | |   | ____/ ___|
  | | | | | | |   |  _| \___ \
  | | | |_| | |___| |___ ___) |
  |_|  \___/|_____|_____|____/

  Instant AI Responses (Ti)
"""

class TulesCommand(click.Command):
    def format_help(self, ctx, formatter):
        console.print(f"[cyan]{TULES_ASCII}[/cyan]")
        super().format_help(ctx, formatter)

def get_ai_response(prompt: str, provider_name: str) -> str:
    """Get response from AI provider using CLI command."""
    try:
        # Determine which command to run
        if provider_name == 'gemini':
            cmd = ['gemini', '-p', prompt]
        elif provider_name == 'claude':
            cmd = ['claude', '-p', prompt]
        else:
            return f"[red]Error: Unknown provider '{provider_name}'[/red]"

        # Run the CLI command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            return f"[red]Error running {provider_name}: {result.stderr}[/red]"

        return result.stdout.strip()

    except FileNotFoundError:
        return f"[red]Error: {provider_name} CLI not found. Please install it first.[/red]"
    except subprocess.TimeoutExpired:
        return "[red]Error: Command timed out after 2 minutes[/red]"
    except Exception as e:
        return f"[red]Error: {str(e)}[/red]"


@click.command(cls=TulesCommand)
@click.argument('prompt', required=False)
@click.option('--provider', type=click.Choice(['gemini', 'claude', 'auto']), default='auto',
              help='AI provider to use (default: auto-detect)')
@click.option('--stdin', is_flag=True, help='Read prompt from stdin')
def instant(prompt: str, provider: str, stdin: bool):
    """
    Tules-instant - Get instant AI responses with rich formatting

    Examples:
        Tules-instant "What is 2+2?"
        Ti "Explain recursion"
        echo "Write a haiku" | Ti --stdin
        Ti --provider claude "Write a poem"
    """

    # Get prompt from stdin if requested
    if stdin:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        else:
            console.print("[red]Error: --stdin flag used but no input on stdin[/red]")
            sys.exit(1)

    # Require prompt
    if not prompt:
        console.print("[red]Error: Prompt required (either as argument or via --stdin)[/red]")
        console.print("\nUsage: Tules-instant \"your prompt here\"")
        console.print("       Ti \"your prompt here\"")
        sys.exit(1)

    # Auto-detect provider if needed
    if provider == 'auto':
        detected = detect_provider()
        if detected:
            provider = detected.get_name().lower()
        else:
            console.print("[red]Error: No AI provider found. Please install gemini or claude CLI.[/red]")
            sys.exit(1)

    # Show which provider we're using
    console.print(f"[dim]Using {provider}...[/dim]\n")

    # Get response from provider
    response = get_ai_response(prompt, provider)

    # Render response with rich formatting
    render_response(response)


if __name__ == '__main__':
    instant()
