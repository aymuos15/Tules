#!/usr/bin/env python3
"""
AI Provider Abstraction Layer
Supports both Claude Code and Gemini CLI backends
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime


class AIProvider(ABC):
    """Base class for AI CLI providers"""

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name"""
        pass

    @abstractmethod
    def get_binary_path(self) -> Optional[str]:
        """Get path to CLI binary"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the system"""
        pass

    @abstractmethod
    def get_config_dir(self) -> Path:
        """Get provider config directory"""
        pass

    @abstractmethod
    def get_bg_agents_dir(self) -> Path:
        """Get background agents directory"""
        pass

    @abstractmethod
    def get_run_command(self, prompt: str, session_id: str, output_format: str = 'text') -> List[str]:
        """Get command to run a task"""
        pass

    @abstractmethod
    def get_docker_mounts(self, cwd: str, home: str, binary_path: str) -> List[str]:
        """Get Docker volume mount arguments"""
        pass

    @abstractmethod
    def get_sessions_path(self, working_dir: str) -> Optional[Path]:
        """Get path to sessions directory for a working directory"""
        pass

    @abstractmethod
    def parse_session_file(self, session_path: Path) -> Dict:
        """Parse a session file and return metadata"""
        pass

    @abstractmethod
    def get_resume_command(self, session_id: str, fork: bool = False) -> List[str]:
        """Get command to resume a session"""
        pass

    @abstractmethod
    def find_session_files(self, working_dir: str) -> List[Path]:
        """Find all session files for a working directory"""
        pass


class ClaudeProvider(AIProvider):
    """Claude Code CLI provider"""

    def get_name(self) -> str:
        return "claude"

    def get_binary_path(self) -> Optional[str]:
        """Find Claude binary"""
        # Common locations
        candidates = [
            Path.home() / '.local' / 'bin' / 'claude',
            Path('/usr/local/bin/claude'),
            Path('/usr/bin/claude')
        ]

        for path in candidates:
            if path.exists() and os.access(path, os.X_OK):
                return str(path)

        # Try which command
        try:
            result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def is_available(self) -> bool:
        return self.get_binary_path() is not None

    def get_config_dir(self) -> Path:
        return Path.home() / '.claude'

    def get_bg_agents_dir(self) -> Path:
        return self.get_config_dir() / 'bg-agents'

    def get_run_command(self, prompt: str, session_id: str, output_format: str = 'text') -> List[str]:
        return [
            'claude', '-p', prompt,
            '--dangerously-skip-permissions',
            '--session-id', session_id,
            '--output-format', output_format
        ]

    def get_docker_mounts(self, cwd: str, home: str, binary_path: str) -> List[str]:
        return [
            '-v', f'{cwd}:/workspace',
            '-v', f'{home}/.claude:{home}/.claude',
            '-v', f'{home}/.claude.json:{home}/.claude.json',
            '-v', f'{binary_path}:/usr/local/bin/claude:ro',
            '-v', f'{home}/.local/share/claude:{home}/.local/share/claude:ro',
        ]

    def _encode_directory(self, path: str) -> str:
        """Encode directory path for Claude storage (/ -> -)"""
        return path.replace('/', '-')

    def get_sessions_path(self, working_dir: str) -> Optional[Path]:
        """Get Claude sessions directory"""
        encoded = self._encode_directory(os.path.abspath(working_dir))
        path = self.get_config_dir() / 'projects' / encoded
        return path if path.exists() else None

    def find_session_files(self, working_dir: str) -> List[Path]:
        """Find all Claude session files (JSONL)"""
        sessions_path = self.get_sessions_path(working_dir)
        if not sessions_path:
            return []

        return list(sessions_path.glob('*.jsonl'))

    def parse_session_file(self, session_path: Path) -> Dict:
        """Parse Claude JSONL session file"""
        metadata = {
            'id': session_path.stem,
            'summary': 'No summary',
            'cwd': None,
            'git_branch': None,
            'timestamp': datetime.fromtimestamp(session_path.stat().st_mtime),
            'is_agent': session_path.stem.startswith('agent-'),
            'messages': []
        }

        try:
            with open(session_path, 'r') as f:
                # First line typically has summary
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)
                    metadata['summary'] = data.get('summary', 'No summary')
                    metadata['cwd'] = data.get('cwd')
                    metadata['git_branch'] = data.get('gitBranch')

                # Parse remaining messages
                f.seek(0)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get('type') in ['user', 'assistant']:
                                metadata['messages'].append(data)
                        except json.JSONDecodeError:
                            continue
        except (IOError, json.JSONDecodeError):
            pass

        return metadata

    def get_resume_command(self, session_id: str, fork: bool = False) -> List[str]:
        cmd = ['claude', '--resume', session_id]
        if fork:
            cmd.append('--fork-session')
        return cmd


class GeminiProvider(AIProvider):
    """Gemini CLI provider"""

    def get_name(self) -> str:
        return "gemini"

    def get_binary_path(self) -> Optional[str]:
        """Find Gemini binary"""
        # Common locations for npm global installs
        candidates = [
            Path.home() / '.npm-global' / 'bin' / 'gemini',
            Path.home() / '.nvm' / 'versions' / 'node' / '*' / 'bin' / 'gemini',
            Path('/usr/local/bin/gemini'),
            Path('/usr/bin/gemini')
        ]

        for path in candidates:
            if '*' in str(path):
                # Handle glob patterns
                import glob
                matches = glob.glob(str(path))
                if matches:
                    path = Path(matches[0])

            if path.exists() and os.access(path, os.X_OK):
                return str(path)

        # Try which command
        try:
            result = subprocess.run(['which', 'gemini'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def is_available(self) -> bool:
        return self.get_binary_path() is not None

    def get_config_dir(self) -> Path:
        return Path.home() / '.gemini'

    def get_bg_agents_dir(self) -> Path:
        return self.get_config_dir() / 'bg-agents'

    def get_run_command(self, prompt: str, session_id: str, output_format: str = 'text') -> List[str]:
        # Note: Gemini doesn't support custom session IDs
        # The session_id parameter is ignored but kept for API compatibility
        return [
            'gemini', '-p', prompt,
            '-y',  # Auto-accept (yolo mode) - equivalent to --dangerously-skip-permissions
            '-o', output_format
        ]

    def get_docker_mounts(self, cwd: str, home: str, binary_path: str) -> List[str]:
        return [
            '-v', f'{cwd}:/workspace',
            '-v', f'{home}/.gemini:{home}/.gemini',
            '-v', f'{binary_path}:/usr/local/bin/gemini:ro',
        ]

    def _hash_directory(self, path: str) -> str:
        """Hash directory path for Gemini storage (SHA-256)"""
        return hashlib.sha256(path.encode('utf-8')).hexdigest()

    def get_sessions_path(self, working_dir: str) -> Optional[Path]:
        """Get Gemini sessions directory"""
        project_hash = self._hash_directory(os.path.abspath(working_dir))
        path = self.get_config_dir() / 'tmp' / project_hash / 'chats'
        return path if path.exists() else None

    def find_session_files(self, working_dir: str) -> List[Path]:
        """Find all Gemini session files (JSON)"""
        sessions_path = self.get_sessions_path(working_dir)
        if not sessions_path:
            return []

        return list(sessions_path.glob('session-*.json'))

    def parse_session_file(self, session_path: Path) -> Dict:
        """Parse Gemini JSON session file"""
        metadata = {
            'id': None,
            'summary': 'No summary',
            'cwd': None,
            'git_branch': None,
            'timestamp': datetime.fromtimestamp(session_path.stat().st_mtime),
            'is_agent': False,
            'messages': []
        }

        try:
            with open(session_path, 'r') as f:
                data = json.load(f)

                metadata['id'] = data.get('sessionId', session_path.stem)

                # Parse timestamp - handle ISO format with 'Z' suffix
                start_time = data.get('startTime')
                if start_time:
                    try:
                        # Remove 'Z' and parse
                        start_time = start_time.replace('Z', '+00:00')
                        metadata['timestamp'] = datetime.fromisoformat(start_time)
                    except:
                        # Fall back to file mtime
                        pass

                # Extract messages
                messages = data.get('messages', [])
                metadata['messages'] = messages

                # Generate summary from first user message
                if messages:
                    first_user_msg = next(
                        (msg for msg in messages if msg.get('type') == 'user'),
                        None
                    )
                    if first_user_msg:
                        content = first_user_msg.get('content', '')
                        metadata['summary'] = content[:100] + ('...' if len(content) > 100 else '')

        except (IOError, json.JSONDecodeError):
            pass

        return metadata

    def get_resume_command(self, session_id: str, fork: bool = False) -> List[str]:
        # Gemini doesn't support session forking
        if fork:
            return None  # Indicate not supported
        return ['gemini', '-r', session_id]


def get_provider(name: str) -> Optional[AIProvider]:
    """Get provider instance by name"""
    providers = {
        'claude': ClaudeProvider(),
        'gemini': GeminiProvider()
    }
    return providers.get(name.lower())


def detect_provider() -> Optional[AIProvider]:
    """Auto-detect available provider (prefers Claude)"""
    # Try Claude first (original default)
    claude = ClaudeProvider()
    if claude.is_available():
        return claude

    # Fall back to Gemini
    gemini = GeminiProvider()
    if gemini.is_available():
        return gemini

    return None


def get_all_providers() -> List[AIProvider]:
    """Get all available providers"""
    providers = [ClaudeProvider(), GeminiProvider()]
    return [p for p in providers if p.is_available()]
