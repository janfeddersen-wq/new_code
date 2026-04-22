"""Browser tools for terminal automation.

This module provides browser-based terminal automation tools,
including Chrome DevTools Protocol (CDP) support.

Note: CDP-based tools require the 'websockets' package to be installed.
Playwright-based tools are deprecated in favor of CDP.
"""

from newcode.config import get_banner_color

# Browser workflows (markdown workflow management - not Playwright-specific)
# Note: This uses file-based storage, not browser-specific
from .browser_workflows import (
    register_list_workflows,
    register_read_workflow,
    register_save_workflow,
)

# Chrome detector (used for both CDP and legacy browser detection)
from .chrome_detector import (
    detect_chrome_executable,
    find_chrome,
    find_playwright_chromium,
    get_chrome_info,
    get_chrome_version,
    is_chrome_available,
)

# Try to import CDP-based tools (requires websockets)
# If websockets is not installed, these imports will fail gracefully
try:
    from .cdp_client import (
        CDPClient,
        CDPClientError,
        CDPCommand,
        CDPCommandError,
        CDPConnectionError,
        CDPEvent,
        CDPResponse,
        EventCallback,
    )
    from .cdp_control import (
        close_browser,
        create_new_page,
        get_browser_status,
        initialize_browser,
        list_pages,
        register_close_browser,
        register_create_new_page,
        register_get_browser_status,
        register_initialize_browser,
        register_list_pages,
    )
    from .cdp_domains import (
        CDPFrame,
        CDPNode,
        DOMDomain,
        InputDomain,
        PageDomain,
        RuntimeDomain,
        TargetDomain,
    )
    from .cdp_interactions import (
        check_element,
        click_element,
        double_click_element,
        get_element_text,
        get_element_value,
        hover_element,
        register_browser_check,
        register_browser_uncheck,
        register_click_element,
        register_double_click_element,
        register_get_element_text,
        register_get_element_value,
        register_hover_element,
        register_select_option,
        register_set_element_text,
        select_option,
        set_element_text,
        uncheck_element,
    )
    from .cdp_locators import (
        find_buttons,
        find_by_label,
        find_by_placeholder,
        find_by_role,
        find_by_test_id,
        find_by_text,
        find_links,
        register_find_buttons,
        register_find_by_label,
        register_find_by_placeholder,
        register_find_by_role,
        register_find_by_test_id,
        register_find_by_text,
        register_find_links,
        register_run_xpath_query,
        run_xpath_query,
    )
    from .cdp_manager import (
        CDPManager,
        cleanup_all_cdp_browsers,
        find_available_port,
        get_cdp_manager,
        get_cdp_session,
        get_session_cdp_manager,
        set_cdp_session,
    )
    from .cdp_navigation import (
        get_page_info,
        go_back,
        go_forward,
        navigate_to_url,
        register_browser_go_back,
        register_browser_go_forward,
        register_get_page_info,
        register_navigate_to_url,
        register_reload_page,
        register_wait_for_load_state,
        reload_page,
        wait_for_load_state,
    )
    from .cdp_screenshot import (
        register_take_screenshot_and_analyze,
        take_screenshot,
    )
    from .cdp_scripts import (
        clear_highlights,
        execute_javascript,
        highlight_element,
        register_browser_clear_highlights,
        register_browser_highlight_element,
        register_execute_javascript,
        register_scroll_page,
        register_scroll_to_element,
        register_set_viewport_size,
        register_wait_for_element,
        scroll_page,
        scroll_to_element,
        set_viewport_size,
        wait_for_element,
    )

    _CDP_AVAILABLE = True
except ImportError:
    # websockets not installed - CDP tools unavailable
    _CDP_AVAILABLE = False

    # Define placeholder classes/functions for type checking
    class CDPClient:  # type: ignore
        """CDPClient requires 'websockets' package."""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                "CDPClient requires 'websockets' package. Install with: pip install websockets"
            )

    class CDPClientError(Exception):  # type: ignore
        pass

    class CDPConnectionError(CDPClientError):  # type: ignore
        pass

    class CDPCommandError(CDPClientError):  # type: ignore
        pass

    class CDPCommand:  # type: ignore
        pass

    class CDPResponse:  # type: ignore
        pass

    class CDPEvent:  # type: ignore
        pass

    class EventCallback:  # type: ignore
        pass

    class CDPManager:  # type: ignore
        """CDPManager requires 'websockets' package."""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                "CDPManager requires 'websockets' package. Install with: pip install websockets"
            )

    class CDPNode:  # type: ignore
        pass

    class CDPFrame:  # type: ignore
        pass

    class PageDomain:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PageDomain requires 'websockets' package. Install with: pip install websockets"
            )

    class DOMDomain:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "DOMDomain requires 'websockets' package. Install with: pip install websockets"
            )

    class RuntimeDomain:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "RuntimeDomain requires 'websockets' package. Install with: pip install websockets"
            )

    class InputDomain:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "InputDomain requires 'websockets' package. Install with: pip install websockets"
            )

    class TargetDomain:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "TargetDomain requires 'websockets' package. Install with: pip install websockets"
            )

    # Placeholder functions
    def initialize_browser(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def close_browser(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def get_browser_status(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def create_new_page(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def list_pages(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def navigate_to_url(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def get_page_info(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def go_back(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def go_forward(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def reload_page(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def wait_for_load_state(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_by_role(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_by_text(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_by_label(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_by_placeholder(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_by_test_id(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def run_xpath_query(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_buttons(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def find_links(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def click_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def double_click_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def hover_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def set_element_text(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def get_element_text(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def get_element_value(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def select_option(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def check_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def uncheck_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def take_screenshot(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def execute_javascript(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def scroll_page(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def scroll_to_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def set_viewport_size(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def wait_for_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def highlight_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def clear_highlights(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_initialize_browser(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_close_browser(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_get_browser_status(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_create_new_page(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_list_pages(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_navigate_to_url(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_get_page_info(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_browser_go_back(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_browser_go_forward(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_reload_page(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_wait_for_load_state(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_by_role(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_by_text(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_by_label(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_by_placeholder(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_by_test_id(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_run_xpath_query(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_buttons(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_find_links(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_click_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_double_click_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_hover_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_set_element_text(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_get_element_text(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_get_element_value(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_select_option(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_browser_check(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_browser_uncheck(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_take_screenshot_and_analyze(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_execute_javascript(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_scroll_page(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_scroll_to_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_set_viewport_size(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_wait_for_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_browser_highlight_element(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def register_browser_clear_highlights(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Browser automation requires 'websockets' package. Install with: pip install websockets"
        )

    def get_cdp_manager(*args, **kwargs):  # type: ignore
        raise ImportError(
            "CDP requires 'websockets' package. Install with: pip install websockets"
        )

    def get_session_cdp_manager(*args, **kwargs):  # type: ignore
        raise ImportError(
            "CDP requires 'websockets' package. Install with: pip install websockets"
        )

    def set_cdp_session(*args, **kwargs):  # type: ignore
        raise ImportError(
            "CDP requires 'websockets' package. Install with: pip install websockets"
        )

    def get_cdp_session(*args, **kwargs):  # type: ignore
        raise ImportError(
            "CDP requires 'websockets' package. Install with: pip install websockets"
        )

    def cleanup_all_cdp_browsers(*args, **kwargs):  # type: ignore
        pass  # No-op when CDP is not available

    def find_available_port(*args, **kwargs):  # type: ignore
        raise ImportError(
            "CDP requires 'websockets' package. Install with: pip install websockets"
        )


def format_terminal_banner(text: str) -> str:
    """Format a terminal tool banner with the configured terminal_tool color.

    Returns Rich markup string that can be used with Text.from_markup().

    Args:
        text: The banner text (e.g., "TERMINAL OPEN 🖥️ localhost:8765")

    Returns:
        Rich markup formatted string
    """
    color = get_banner_color("terminal_tool")
    return f"[{color}]╭──[/{color}] [bold]{text.upper()}[/bold] [{color}]───[/{color}]"


__all__ = [
    # Terminal banner
    "format_terminal_banner",
    # Chrome detector
    "get_chrome_info",
    "find_chrome",
    "find_playwright_chromium",
    # Workflow tools
    "register_list_workflows",
    "register_read_workflow",
    "register_save_workflow",
    # CDP availability flag
    "_CDP_AVAILABLE",
    # CDP Client
    "CDPClient",
    "CDPClientError",
    "CDPConnectionError",
    "CDPCommandError",
    "CDPCommand",
    "CDPResponse",
    "CDPEvent",
    "EventCallback",
    # CDP Manager
    "CDPManager",
    "get_cdp_manager",
    "get_session_cdp_manager",
    "set_cdp_session",
    "get_cdp_session",
    "cleanup_all_cdp_browsers",
    "find_available_port",
    # CDP Domains
    "PageDomain",
    "DOMDomain",
    "RuntimeDomain",
    "InputDomain",
    "TargetDomain",
    "CDPNode",
    "CDPFrame",
    # CDP Control Tools
    "initialize_browser",
    "close_browser",
    "get_browser_status",
    "create_new_page",
    "list_pages",
    "register_initialize_browser",
    "register_close_browser",
    "register_get_browser_status",
    "register_create_new_page",
    "register_list_pages",
    # CDP Navigation Tools
    "navigate_to_url",
    "get_page_info",
    "go_back",
    "go_forward",
    "reload_page",
    "wait_for_load_state",
    "register_navigate_to_url",
    "register_get_page_info",
    "register_browser_go_back",
    "register_browser_go_forward",
    "register_reload_page",
    "register_wait_for_load_state",
    # CDP Locators Tools
    "find_by_role",
    "find_by_text",
    "find_by_label",
    "find_by_placeholder",
    "find_by_test_id",
    "run_xpath_query",
    "find_buttons",
    "find_links",
    "register_find_by_role",
    "register_find_by_text",
    "register_find_by_label",
    "register_find_by_placeholder",
    "register_find_by_test_id",
    "register_run_xpath_query",
    "register_find_buttons",
    "register_find_links",
    # CDP Interactions Tools
    "click_element",
    "double_click_element",
    "hover_element",
    "set_element_text",
    "get_element_text",
    "get_element_value",
    "select_option",
    "check_element",
    "uncheck_element",
    "register_click_element",
    "register_double_click_element",
    "register_hover_element",
    "register_set_element_text",
    "register_get_element_text",
    "register_get_element_value",
    "register_select_option",
    "register_browser_check",
    "register_browser_uncheck",
    # CDP Screenshot Tools
    "take_screenshot",
    "register_take_screenshot_and_analyze",
    # CDP Scripts Tools
    "execute_javascript",
    "scroll_page",
    "scroll_to_element",
    "set_viewport_size",
    "wait_for_element",
    "highlight_element",
    "clear_highlights",
    "register_execute_javascript",
    "register_scroll_page",
    "register_scroll_to_element",
    "register_set_viewport_size",
    "register_wait_for_element",
    "register_browser_highlight_element",
    "register_browser_clear_highlights",
    # Chrome detector
    "detect_chrome_executable",
    "is_chrome_available",
    "get_chrome_version",
]
