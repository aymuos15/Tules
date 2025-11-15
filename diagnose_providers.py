#!/usr/bin/env python3
"""Diagnose AI provider availability and configuration."""

import subprocess
import sys
import os
from pathlib import Path

def check_command_in_path(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        result = subprocess.run(
            ['where' if sys.platform == 'win32' else 'which', cmd],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking {cmd}: {e}")
        return False

def get_command_path(cmd: str) -> str:
    """Get full path to a command."""
    try:
        result = subprocess.run(
            ['where' if sys.platform == 'win32' else 'which', cmd],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.returncode == 0 else "Not found"
    except Exception as e:
        return f"Error: {e}"

def test_gemini_command() -> bool:
    """Test if gemini command works."""
    try:
        result = subprocess.run(
            ['gemini', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running gemini: {e}")
        return False

def test_claude_command() -> bool:
    """Test if claude command works."""
    try:
        result = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running claude: {e}")
        return False

def main():
    print("=" * 60)
    print("AI Provider Diagnostic")
    print("=" * 60)
    
    print("\n[ENVIRONMENT]")
    print(f"Python: {sys.executable}")
    print(f"Platform: {sys.platform}")
    print(f"PATH: {os.environ.get('PATH', 'Not set')[:100]}...")
    
    print("\n[GEMINI CLI]")
    gemini_in_path = check_command_in_path('gemini')
    print(f"  In PATH: {gemini_in_path}")
    print(f"  Path: {get_command_path('gemini')}")
    print(f"  Works: {test_gemini_command()}")
    
    print("\n[CLAUDE CLI]")
    claude_in_path = check_command_in_path('claude')
    print(f"  In PATH: {claude_in_path}")
    print(f"  Path: {get_command_path('claude')}")
    print(f"  Works: {test_claude_command()}")
    
    print("\n[PYTHON PACKAGES]")
    try:
        import gemini
        print(f"  gemini package: Found ({gemini.__file__})")
    except ImportError:
        print("  gemini package: Not found")
    
    try:
        import claude
        print(f"  claude package: Found ({claude.__file__})")
    except ImportError:
        print("  claude package: Not found")

    print("\n[AI_PROVIDER MODULE]")
    try:
        from ai_provider import get_provider, get_all_providers, detect_provider
        
        all_providers = get_all_providers()
        print(f"  Total providers: {len(all_providers)}")
        
        for provider in all_providers:
            name = provider.get_name()
            available = provider.is_available()
            print(f"    - {name}: {available}")
        
        detected = detect_provider()
        if detected:
            print(f"  Auto-detected: {detected.get_name()}")
        else:
            print("  Auto-detected: None")
            
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
