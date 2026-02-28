"""Platform abstraction for daemon management.

Provides a unified interface for daemon operations across Windows, Linux, and macOS.
"""

import sys

if sys.platform == "win32":
    from newcode.scheduler.platform_win import (
        is_process_running,
        terminate_process,
    )
else:
    from newcode.scheduler.platform_unix import (
        is_process_running,
        terminate_process,
    )

__all__ = ["is_process_running", "terminate_process"]
