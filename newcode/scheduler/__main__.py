"""Entry point for running scheduler daemon directly.

Usage: python -m newcode.scheduler
"""

from newcode.scheduler.daemon import start_daemon

if __name__ == "__main__":
    start_daemon(foreground=True)
