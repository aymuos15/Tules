# banner.py
import sys
 
TULES_BANNER = r"""
████████╗██╗   ██╗██╗     ███████╗███████╗
╚══██╔══╝██║   ██║██║     ██╔════╝██╔════╝
   ██║   ██║   ██║██║     █████╗  ███████╗
   ██║   ██║   ██║██║     ██╔══╝  ╚════██║
   ██║   ╚██████╔╝███████╗███████╗███████║
   ╚═╝    ╚═════╝ ╚══════╝╚══════╝╚══════╝
"""

def print_banner_tules() -> str:
    """Return banner with 'Background Agent Runner (T)' description."""
    return TULES_BANNER + "\n  Background Agent Runner (T)\n"

def print_banner_instant() -> str:
    """Return banner with 'Instant AI Responses (Ti)' description."""
    return TULES_BANNER + "\n  Instant AI Responses (Ti)\n"

def print_banner_sessions() -> str:
    """Return banner with 'Session Browser (Ts)' description."""
    return TULES_BANNER + "\n  Session Browser (Ts)\n"