#!/usr/bin/env python3
"""AI provider abstraction for Claude and Gemini CLI."""

import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name (e.g., 'Claude', 'Gemini')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the system."""
        pass

    @abstractmethod
    def find_session_files(self, directory: str) -> List[Path]:
        """Find session files in a directory."""
        pass

    @abstractmethod
    def parse_session_file(self, session_path: Path) -> Dict[str, Any]:
        """Parse a session file and return metadata."""
        pass

    @abstractmethod
    def get_bg_agents_dir(self) -> Path:
        """Get the background agents directory."""
        pass

    @abstractmethod
    def get_resume_command(self, session_id: str, fork: bool) -> Optional[List[str]]:
        """Get command to resume a session."""
        pass


class GeminiProvider(AIProvider):
    """Gemini CLI provider."""

    def get_name(self) -> str:
        return "Gemini"

    def is_available(self) -> bool:
        """Check if gemini-cli is available."""
        # Try importing google-generativeai (used by gemini-cli)
        try:
            import google.generativeai
            return True
        except ImportError:
            pass
        
        # Try importing gemini_cli directly
        try:
            import gemini_cli
            return True
        except ImportError:
            pass
        
        # Fall back to checking if 'gemini' command works
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                return "gemini" in output or "version" in output
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return False

    def find_session_files(self, directory: str) -> List[Path]:
        """Find Gemini session files."""
        sessions_dir = Path.home() / ".gemini" / "sessions"
        if not sessions_dir.exists():
            return []

        session_files = list(sessions_dir.glob("*.json"))
        return sorted(session_files, key=lambda p: p.stat().st_mtime, reverse=True)

    def parse_session_file(self, session_path: Path) -> Dict[str, Any]:
        """Parse Gemini session JSON file."""
        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            'id': data.get('id', session_path.stem),
            'summary': data.get('summary', data.get('title', 'Untitled')),
            'cwd': data.get('cwd'),
            'git_branch': data.get('git_branch'),
            'timestamp': datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            'is_agent': data.get('is_agent', False),
            'messages': data.get('messages', []),
        }

    def get_bg_agents_dir(self) -> Path:
        """Get Gemini bg-agents directory."""
        return Path.home() / ".gemini" / "bg-agents"

    def get_resume_command(self, session_id: str, fork: bool) -> Optional[List[str]]:
        """Get command to resume Gemini session."""
        if fork:
            return ["gemini", "--fork", session_id]
        else:
            return ["gemini", "--resume", session_id]


class ClaudeProvider(AIProvider):
    """Claude Code provider (via Anthropic SDK)."""

    def get_name(self) -> str:
        return "Claude"

    def is_available(self) -> bool:
        """Check if Anthropic Claude is available."""
        # Try importing anthropic SDK
        try:
            import anthropic
            return True
        except ImportError:
            pass
        
        # Fall back to checking if 'claude' command works
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return False

    def find_session_files(self, directory: str) -> List[Path]:
        """Find Claude session files."""
        sessions_dir = Path.home() / ".claude" / "sessions"
        if not sessions_dir.exists():
            return []

        session_files = list(sessions_dir.glob("*.json"))
        return sorted(session_files, key=lambda p: p.stat().st_mtime, reverse=True)

    def parse_session_file(self, session_path: Path) -> Dict[str, Any]:
        """Parse Claude session JSON file."""
        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            'id': data.get('id', session_path.stem),
            'summary': data.get('summary', data.get('title', 'Untitled')),
            'cwd': data.get('cwd'),
            'git_branch': data.get('git_branch'),
            'timestamp': datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            'is_agent': data.get('is_agent', False),
            'messages': data.get('messages', []),
        }

    def get_bg_agents_dir(self) -> Path:
        """Get Claude bg-agents directory."""
        return Path.home() / ".claude" / "bg-agents"

    def get_resume_command(self, session_id: str, fork: bool) -> Optional[List[str]]:
        """Get command to resume Claude session."""
        if fork:
            return ["claude", "--fork", session_id]
        else:
            return ["claude", "--resume", session_id]


class MockProvider(AIProvider):
    """Mock provider for testing when no real provider is available."""

    def get_name(self) -> str:
        return "Mock"

    def is_available(self) -> bool:
        """Always available for testing."""
        return True

    def find_session_files(self, directory: str) -> List[Path]:
        """Return mock session files for demo purposes."""
        mock_dir = Path.home() / ".mock_sessions"
        mock_dir.mkdir(exist_ok=True)
        
        # Create sample sessions if directory is empty
        session_files = list(mock_dir.glob("*.json"))
        if not session_files:
            self._create_sample_sessions(mock_dir)
            session_files = list(mock_dir.glob("*.json"))
        
        return sorted(session_files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _create_sample_sessions(self, mock_dir: Path) -> None:
        """Create sample session files for demo."""
        samples = [
            {
                "id": "demo-001",
                "summary": "Test session with Python code review",
                "cwd": str(Path.home()),
                "git_branch": "main",
                "timestamp": datetime.now().isoformat(),
                "is_agent": False,
                "messages": [
                    {"message": {"role": "user", "content": [{"type": "text", "text": "Review this Python code"}]}},
                    {"message": {"role": "assistant", "content": [{"type": "text", "text": "This looks good overall. Consider adding type hints."}]}},
                ],
            },
            {
                "id": "demo-002",
                "summary": "Background agent running task",
                "cwd": str(Path.home() / "projects"),
                "git_branch": "feature/new-api",
                "timestamp": datetime.now().isoformat(),
                "is_agent": True,
                "messages": [
                    {"message": {"role": "user", "content": [{"type": "text", "text": "Implement REST API"}]}},
                ],
            },
            {
                "id": "demo-003",
                "summary": "Documentation generation session",
                "cwd": str(Path.home() / "docs"),
                "git_branch": "main",
                "timestamp": datetime.now().isoformat(),
                "is_agent": False,
                "messages": [
                    {"message": {"role": "user", "content": [{"type": "text", "text": "Generate API docs"}]}},
                    {"message": {"role": "assistant", "content": [{"type": "text", "text": "# API Documentation\n\nGenerated successfully."}]}},
                ],
            },
        ]
        
        for sample in samples:
            session_file = mock_dir / f"{sample['id']}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(sample, f, indent=2)

    def parse_session_file(self, session_path: Path) -> Dict[str, Any]:
        """Parse mock session file."""
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}

        return {
            'id': data.get('id', session_path.stem[:8]),
            'summary': data.get('summary', f"Session: {session_path.name}"),
            'cwd': data.get('cwd'),
            'git_branch': data.get('git_branch'),
            'timestamp': datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            'is_agent': data.get('is_agent', False),
            'messages': data.get('messages', []),
        }

    def get_bg_agents_dir(self) -> Path:
        """Get mock bg-agents directory."""
        return Path.home() / ".mock_sessions" / "bg-agents"

    def get_resume_command(self, session_id: str, fork: bool) -> Optional[List[str]]:
        """Mock doesn't support resume."""
        return None


def get_all_providers() -> List[AIProvider]:
    """Get all available providers."""
    return [GeminiProvider(), ClaudeProvider(), MockProvider()]


def get_provider(name: str) -> Optional[AIProvider]:
    """Get a specific provider by name."""
    name_lower = name.lower()
    for provider in get_all_providers():
        if provider.get_name().lower() == name_lower:
            return provider
    return None


def detect_provider() -> Optional[AIProvider]:
    """Auto-detect an available provider (prefer real over mock)."""
    for provider in [GeminiProvider(), ClaudeProvider()]:
        if provider.is_available():
            return provider
    
    # Fall back to mock if no real provider
    return MockProvider()
