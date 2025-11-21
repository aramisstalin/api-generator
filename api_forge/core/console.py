"""
Shared Rich console for consistent CLI output across the application.
"""

from rich.console import Console

# Global console instance
console = Console()

__all__ = ["console"]