#!/usr/bin/env python3
"""
Tules-instant - Instant AI CLI with rich rendering

Quick interactive AI responses using SDKs (not background agents).
Supports both Gemini and Claude with automatic provider detection.
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel

from tui_renderer import render_response

console = Console()


def get_gemini_response(prompt: str) -> str:
    """Get response from Gemini using SDK."""
    try:
        import google.generativeai as genai
        import os

        # Configure API key from environment
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "[red]Error: GEMINI_API_KEY environment variable not set[/red]"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        return "[red]Error: google-generativeai package not installed. Run: pip install google-generativeai[/red]"
    except Exception as e:
        return f"[red]Error: {str(e)}[/red]"


def get_claude_response(prompt: str) -> str:
    """Get response from Claude using SDK."""
    try:
        import anthropic
        import os

        # Configure API key from environment
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]"

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract text from content blocks
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        return response_text
    except ImportError:
        return "[red]Error: anthropic package not installed. Run: pip install anthropic[/red]"
    except Exception as e:
        return f"[red]Error: {str(e)}[/red]"


def detect_provider() -> str:
    """Detect which provider is available."""
    import os

    # Check for API keys
    has_gemini = os.environ.get('GEMINI_API_KEY') is not None
    has_claude = os.environ.get('ANTHROPIC_API_KEY') is not None

    # Check for packages
    try:
        import google.generativeai
        has_gemini_pkg = True
    except ImportError:
        has_gemini_pkg = False

    try:
        import anthropic
        has_claude_pkg = True
    except ImportError:
        has_claude_pkg = False

    # Prefer Gemini, fallback to Claude
    if has_gemini and has_gemini_pkg:
        return 'gemini'
    elif has_claude and has_claude_pkg:
        return 'claude'
    elif has_gemini_pkg:
        return 'gemini'  # Package available, will show API key error
    elif has_claude_pkg:
        return 'claude'  # Package available, will show API key error
    else:
        return 'gemini'  # Default, will show package install error


@click.command()
@click.argument('prompt', required=False)
@click.option('--provider', type=click.Choice(['gemini', 'claude', 'auto']), default='auto',
              help='AI provider to use (default: auto-detect)')
@click.option('--stdin', is_flag=True, help='Read prompt from stdin')
def instant(prompt: str, provider: str, stdin: bool):
    """
    Tules-instant - Get instant AI responses with rich formatting

    Examples:
        Tules-instant "What is 2+2?"
        echo "Explain recursion" | Tules-instant --stdin
        Tules-instant --provider claude "Write a haiku"
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
        sys.exit(1)

    # Auto-detect provider if needed
    if provider == 'auto':
        provider = detect_provider()

    # Show which provider we're using
    console.print(f"[dim]Using {provider}...[/dim]\n")

    # Get response from provider
    if provider == 'gemini':
        response = get_gemini_response(prompt)
    elif provider == 'claude':
        response = get_claude_response(prompt)
    else:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        sys.exit(1)

    # Render response with rich formatting
    render_response(response)


if __name__ == '__main__':
    instant()
