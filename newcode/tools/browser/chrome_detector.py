"""OS-agnostic Chrome/Chromium detection utilities.

This module provides functions to detect Chrome/Chromium executables across
Windows, macOS, and Linux. It prioritizes system-installed Chrome when available,
following the user's preference (via browser_chrome_path config), then falls back
to Playwright's bundled Chromium if no system Chrome is found.

Example:
    >>> from newcode.tools.browser.chrome_detector import (
    ...     detect_chrome_executable,
    ...     is_chrome_available,
    ...     get_chrome_version,
    ... )
    >>> # Quick check
    >>> if is_chrome_available():
    ...     path = detect_chrome_executable()
    ...     version = get_chrome_version(path)
    ...     print(f"Found Chrome {version} at {path}")
    >>> # Find Playwright's bundled Chromium specifically
    >>> from newcode.tools.browser.chrome_detector import find_playwright_chromium
    >>> pw_chrome = find_playwright_chromium()
"""

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from newcode.messaging import emit_info, emit_warning

# Platform-specific Playwright cache paths
_PLAYWRIGHT_CACHE_PATHS = {
    "Windows": Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright",
    "Darwin": Path.home() / "Library/Caches/ms-playwright",  # macOS
    "Linux": Path.home() / ".cache/ms-playwright",
}

# Platform-specific Chrome executable names/paths
_CHROME_PATHS = {
    "Windows": [
        # Common installation paths
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe",
        # Microsoft Edge (Chromium-based, fallback)
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "Darwin": [
        # Google Chrome
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chrome.app/Contents/MacOS/Chrome",
        # Chromium
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        # Microsoft Edge
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ],
    "Linux": [
        # Common binary names will be checked via which
    ],
}

_LINUX_CHROME_BINARIES = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "microsoft-edge-stable",
]


def _get_platform() -> str:
    """Get the current platform name.

    Returns:
        Platform name: "Windows", "Darwin" (macOS), or "Linux".
    """
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Darwin":
        return "Darwin"
    else:
        return "Linux"


def _is_executable(path: str) -> bool:
    """Check if a path is an executable file.

    Args:
        path: Path to check.

    Returns:
        True if the path exists and is executable.
    """
    if not path:
        return False

    p = Path(path)
    if not p.exists():
        return False

    # On Windows, check if it's a file (executability is implicit for .exe)
    if _get_platform() == "Windows":
        return p.is_file()

    # On Unix-like systems, check execute permission
    return os.access(p, os.X_OK)


def _expand_windows_path(path: str) -> str:
    """Expand Windows environment variables in a path.

    Args:
        path: Path that may contain %VARNAME% patterns.

    Returns:
        Path with environment variables expanded.
    """
    # Expand %USERNAME% and other Windows env vars
    result = path
    for var in re.findall(r"%([^%]+)%", path):
        value = os.environ.get(var, "")
        result = result.replace(f"%{var}%", value)
    return result


def _which(command: str) -> Optional[str]:
    """Cross-platform which command.

    Args:
        command: Command to find.

    Returns:
        Full path to the command if found, None otherwise.
    """
    return shutil.which(command)


def find_playwright_chromium() -> Optional[str]:
    """Find Playwright's bundled Chromium executable.

    Searches the platform-specific Playwright cache directories for
    Chromium installations.

    Returns:
        Path to Playwright's Chromium executable if found, None otherwise.

    Example:
        >>> chrome_path = find_playwright_chromium()
        >>> if chrome_path:
        ...     print(f"Found Playwright Chromium at {chrome_path}")
    """
    platform_name = _get_platform()
    cache_dir = _PLAYWRIGHT_CACHE_PATHS.get(platform_name)

    if not cache_dir or not cache_dir.exists():
        emit_info(f"Playwright cache directory not found: {cache_dir}")
        return None

    emit_info(f"Searching for Playwright Chromium in {cache_dir}")

    # Search for chromium-* directories
    chromium_dirs = sorted(cache_dir.glob("chromium-*"), reverse=True)

    if not chromium_dirs:
        emit_info("No Chromium directories found in Playwright cache")
        return None

    # Determine the expected executable path based on platform
    if platform_name == "Windows":
        exe_patterns = ["chrome-win/chrome.exe", "chrome-win32/chrome.exe"]
    elif platform_name == "Darwin":
        exe_patterns = [
            "chrome-mac/Chromium.app/Contents/MacOS/Chromium",
            "chrome-mac/Chromium.app/Contents/MacOS/Google Chrome",
        ]
    else:  # Linux
        exe_patterns = ["chrome-linux/chrome", "chrome-linux/chromium"]

    # Check each chromium directory (newest first)
    for chromium_dir in chromium_dirs:
        for pattern in exe_patterns:
            exe_path = chromium_dir / pattern
            if exe_path.exists() and _is_executable(str(exe_path)):
                emit_info(f"Found Playwright Chromium: {exe_path}")
                return str(exe_path)

    emit_info("Playwright Chromium found in cache but executable not located")
    return None


def _get_windows_chrome_from_registry() -> Optional[str]:
    """Get Chrome path from Windows registry.

    Checks both HKLM and HKCU for Chrome installation information.

    Returns:
        Path to Chrome if found in registry, None otherwise.
    """
    try:
        import winreg
    except ImportError:
        return None

    # Registry paths to check (in order of preference)
    registry_paths = [
        # HKLM - Machine-wide installation
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome",
        ),
        # HKCU - User installation
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome",
        ),
    ]

    for hkey, subkey in registry_paths:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                if "App Paths" in subkey:
                    # App Paths key stores the executable path directly
                    value, _ = winreg.QueryValueEx(key, None)
                    if value and Path(value).exists():
                        return value
                else:
                    # Uninstall key stores InstallLocation
                    try:
                        install_location, _ = winreg.QueryValueEx(
                            key, "InstallLocation"
                        )
                        if install_location:
                            exe_path = Path(install_location) / "chrome.exe"
                            if exe_path.exists():
                                return str(exe_path)
                    except FileNotFoundError:
                        pass

                    # Try DisplayIcon
                    try:
                        display_icon, _ = winreg.QueryValueEx(key, "DisplayIcon")
                        if display_icon and "," in display_icon:
                            # DisplayIcon format: "path,icon_index"
                            exe_path = display_icon.split(",")[0]
                            if Path(exe_path).exists():
                                return exe_path
                    except FileNotFoundError:
                        pass
        except (OSError, FileNotFoundError):
            continue

    return None


def _find_system_chrome() -> Optional[str]:
    """Find system-installed Chrome/Chromium (non-Playwright).

    Platform-specific detection:
    - Windows: Registry checks, then common paths
    - macOS: Applications folder, then PATH
    - Linux: PATH lookups for common binary names

    Returns:
        Path to Chrome/Chromium executable if found, None otherwise.
    """
    platform_name = _get_platform()

    if platform_name == "Windows":
        # First try registry
        emit_info("Checking Windows registry for Chrome installation...")
        registry_path = _get_windows_chrome_from_registry()
        if registry_path:
            emit_info(f"Found Chrome in registry: {registry_path}")
            return registry_path

        # Then check common paths
        emit_info("Checking common Windows installation paths...")
        for path_template in _CHROME_PATHS["Windows"]:
            path = _expand_windows_path(path_template)
            if _is_executable(path):
                emit_info(f"Found Chrome at: {path}")
                return path

    elif platform_name == "Darwin":
        # Check macOS application paths
        emit_info("Checking macOS Applications folder...")
        for path in _CHROME_PATHS["Darwin"]:
            if _is_executable(path):
                emit_info(f"Found Chrome at: {path}")
                return path

        # Check PATH for google-chrome
        emit_info("Checking PATH for google-chrome...")
        path = _which("google-chrome")
        if path:
            emit_info(f"Found google-chrome in PATH: {path}")
            return path

    else:  # Linux
        # Check common binary names
        emit_info("Checking PATH for Chrome/Chromium binaries...")
        for binary in _LINUX_CHROME_BINARIES:
            path = _which(binary)
            if path:
                emit_info(f"Found {binary} in PATH: {path}")
                return path

    return None


def detect_chrome_executable() -> Optional[str]:
    """Detect Chrome/Chromium executable across all platforms.

    Detection strategy (in order of preference):
    1. Configured custom Chrome path (browser_chrome_path config)
    2. System Chrome/Chromium installation (via _find_system_chrome)
    3. Playwright's bundled Chromium (fallback for compatibility)

    This order prioritizes user configuration and system Chrome, using
    Playwright only as a last resort when no system Chrome is available.

    Returns:
        Path to the Chrome/Chromium executable if found, None otherwise.

    Example:
        >>> chrome_path = detect_chrome_executable()
        >>> if chrome_path:
        ...     print(f"Using Chrome at: {chrome_path}")
        ... else:
        ...     print("Chrome not found")
    """
    emit_info("Detecting Chrome/Chromium executable...")

    # First priority: Configured custom Chrome path
    try:
        from newcode.config import get_browser_chrome_path

        custom_path = get_browser_chrome_path()
        if custom_path:
            emit_info(f"Using configured Chrome path: {custom_path}")
            if _is_executable(custom_path):
                emit_info(f"Configured Chrome path verified: {custom_path}")
                return custom_path
            emit_warning(f"Configured Chrome path not executable: {custom_path}")
    except Exception as e:
        emit_info(f"Could not read browser_chrome_path config: {e}")

    # Second priority: System Chrome/Chromium
    emit_info("Checking for system Chrome/Chromium installation...")
    system_chrome = _find_system_chrome()
    if system_chrome:
        emit_info(f"Using system Chrome/Chromium: {system_chrome}")
        return system_chrome

    emit_warning("System Chrome not found, falling back to Playwright Chromium")

    # Third priority: Playwright's bundled Chromium
    emit_info("Checking for Playwright's bundled Chromium...")
    playwright_chrome = find_playwright_chromium()
    if playwright_chrome:
        emit_info(f"Using Playwright Chromium: {playwright_chrome}")
        return playwright_chrome

    emit_warning("No Chrome/Chromium installation found")
    emit_info("Tip: Install Chrome or Chromium, or set browser_chrome_path in config")
    return None


def is_chrome_available() -> bool:
    """Quick check if any Chrome/Chromium is available.

    This is a lightweight check that can be used to determine
    if browser automation is possible without full path resolution.

    Returns:
        True if any Chrome/Chromium executable is found, False otherwise.

    Example:
        >>> if is_chrome_available():
        ...     # Proceed with browser automation
        ... else:
        ...     # Handle missing Chrome
    """
    return detect_chrome_executable() is not None


def get_chrome_version(executable_path: str) -> Optional[str]:
    """Get the version of Chrome/Chromium at the given path.

    Attempts to extract version information by running the executable
    with the --version flag.

    Args:
        executable_path: Path to the Chrome/Chromium executable.

    Returns:
        Version string (e.g., "120.0.6099.109") if successfully parsed,
        None otherwise.

    Example:
        >>> version = get_chrome_version("/usr/bin/google-chrome")
        >>> if version:
        ...     print(f"Chrome version: {version}")
    """
    if not executable_path or not _is_executable(executable_path):
        emit_warning(f"Invalid executable path: {executable_path}")
        return None

    try:
        # Run chrome --version
        result = subprocess.run(
            [executable_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            emit_warning(f"Failed to get Chrome version: {result.stderr}")
            return None

        # Parse version from output
        # Output format: "Google Chrome 120.0.6099.109" or "Chromium 120.0.6099.109"
        output = result.stdout.strip()
        emit_info(f"Chrome version output: {output}")

        # Extract version number using regex
        version_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
        if version_match:
            version = version_match.group(1)
            emit_info(f"Parsed Chrome version: {version}")
            return version

        # Fallback: try to extract any version-like string
        version_match = re.search(r"(\d+\.\d+(?:\.\d+)*)", output)
        if version_match:
            return version_match.group(1)

        emit_warning(f"Could not parse version from: {output}")
        return None

    except subprocess.TimeoutExpired:
        emit_warning("Timeout while getting Chrome version")
        return None
    except Exception as e:
        emit_warning(f"Error getting Chrome version: {e}")
        return None


def get_chrome_info() -> dict:
    """Get comprehensive information about available Chrome/Chromium.

    Returns:
        Dictionary containing:
        - 'available': bool - Whether Chrome is available
        - 'path': Optional[str] - Path to Chrome executable
        - 'version': Optional[str] - Chrome version string
        - 'is_playwright': bool - Whether using Playwright's bundled Chromium
        - 'platform': str - Current platform name

    Example:
        >>> info = get_chrome_info()
        >>> if info['available']:
        ...     print(f"Chrome {info['version']} at {info['path']}")
    """
    path = detect_chrome_executable()
    platform_name = _get_platform()

    if not path:
        return {
            "available": False,
            "path": None,
            "version": None,
            "is_playwright": False,
            "platform": platform_name,
        }

    # Check if this is Playwright's Chromium
    is_playwright = "ms-playwright" in path or ".cache/ms-playwright" in path

    version = get_chrome_version(path)

    return {
        "available": True,
        "path": path,
        "version": version,
        "is_playwright": is_playwright,
        "platform": platform_name,
    }


# Backwards compatibility alias
find_chrome = detect_chrome_executable


__all__ = [
    "detect_chrome_executable",
    "is_chrome_available",
    "get_chrome_version",
    "get_chrome_info",
    "find_playwright_chromium",
    "find_chrome",  # Alias for backwards compatibility
]
