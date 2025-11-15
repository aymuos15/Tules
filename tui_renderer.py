import argparse
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax


console = Console()


# ---------------------------------------------------------------------------
# Block model
# ---------------------------------------------------------------------------

@dataclass
class TextBlock:
    """Arbitrary markdown text (no fenced code)."""
    markdown: str


@dataclass
class CodeBlock:
    """A fenced code block ```lang ... ```."""
    language: Optional[str]
    code: str


Block = Union[TextBlock, CodeBlock]


# ---------------------------------------------------------------------------
# Parsing: split markdown into text + fenced code blocks
# ---------------------------------------------------------------------------

FENCE_PATTERN = re.compile(
    r"```(\w+)?\s*\n(.*?)```",
    re.DOTALL,
)


def split_markdown_and_code(text: str) -> List[Block]:
    """
    Split the markdown into TextBlock and CodeBlock chunks by
    looking for fenced code blocks.
    """
    blocks: List[Block] = []
    last_end = 0

    for match in FENCE_PATTERN.finditer(text):
        start, end = match.span()

        # 1. Text before this code block
        if start > last_end:
            before = text[last_end:start]
            if before.strip():
                blocks.append(TextBlock(markdown=before))

        # 2. The code block itself
        language = match.group(1)
        code = match.group(2).rstrip("\n")
        blocks.append(CodeBlock(language=language, code=code))

        last_end = end

    # 3. Trailing text after the last code block
    if last_end < len(text):
        tail = text[last_end:]
        if tail.strip():
            blocks.append(TextBlock(markdown=tail))

    return blocks


# ---------------------------------------------------------------------------
# Markdown normalisation (left-align headings)
# ---------------------------------------------------------------------------

HEADING_LINE = re.compile(r"^(#+)\s+(.*)")


def normalize_markdown(md: str) -> str:
    """
    Convert Markdown headings to bold text so Rich doesn't center them.
    """
    lines = []
    for line in md.splitlines():
        m = HEADING_LINE.match(line)
        if m:
            text = m.group(2)
            lines.append(f"**{text}**")
        else:
            lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_blocks(blocks: List[Block]) -> None:
    for block in blocks:
        if isinstance(block, TextBlock):
            md_text = normalize_markdown(block.markdown)
            md = Markdown(
                md_text,
                code_theme="monokai",
                hyperlinks=True,
            )
            console.print(md)
            console.print()  # blank line

        elif isinstance(block, CodeBlock):
            lang = block.language or "text"
            syntax = Syntax(
                block.code,
                lang,
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
            )

            title = f"[bold cyan]{lang}[/bold cyan]   [black on bright_white] COPY [/black on bright_white]"

            console.print(
                Panel(
                    syntax,
                    title=title,
                    border_style="cyan",
                    padding=(0, 1),
                    expand=False,
                )
            )


def render_response(text: str) -> None:
    """Render markdown response with code blocks."""
    blocks = split_markdown_and_code(text)
    render_blocks(blocks)

# ---------------------------------------------------------------------------
# CLI glue (stdin-only)
# ---------------------------------------------------------------------------

def read_stdin() -> Optional[str]:
    """Read all data from stdin if it exists. If no pipe, return None."""
    if sys.stdin.isatty():
        return None
    data = sys.stdin.read()
    return data if data.strip() else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render markdown (e.g. Gemini output) with rich formatting."
    )
    # No positional prompt; stdin-only to avoid confusion.
    return parser.parse_args()


def main() -> None:
    _ = parse_args()  # reserved for future flags

    stdin_text = read_stdin()
    if stdin_text is None:
        console.print(
            "[bold red]No input on stdin.[/bold red]\n\n"
            "Usage example:\n"
            '  gemini -p "your prompt" | python gemini_tui.py\n'
        )
        sys.exit(1)

    blocks = split_markdown_and_code(stdin_text)
    render_blocks(blocks)


if __name__ == "__main__":
    main()
