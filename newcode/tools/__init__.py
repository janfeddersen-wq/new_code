"""Tools module - CDP-based browser automation tools.

This module provides tool registration for the agent system.
All browser automation tools now use Chrome DevTools Protocol (CDP)
instead of Playwright for direct browser control.

Note: CDP-based tools require the 'websockets' package to be installed.
Install with: pip install websockets
"""

from newcode.callbacks import on_register_tools
from newcode.messaging import emit_warning
from newcode.tools.agent_tools import register_invoke_agent, register_list_agents
from newcode.tools.ask_user_question import register_ask_user_question
from newcode.tools.browser.browser_workflows import (
    register_list_workflows,
    register_read_workflow,
    register_save_workflow,
)

# Terminal automation tools
# Terminal automation tools (not browser-specific, separate from CDP)
from newcode.tools.browser.terminal_command_tools import (
    register_run_terminal_command,
    register_send_terminal_keys,
    register_wait_terminal_output,
)
from newcode.tools.browser.terminal_screenshot_tools import (
    register_load_image,
    register_terminal_compare_mockup,
    register_terminal_read_output,
    register_terminal_screenshot,
)
from newcode.tools.browser.terminal_tools import (
    register_check_terminal_server,
    register_close_terminal,
    register_open_terminal,
    register_start_api_server,
)
from newcode.tools.command_runner import register_agent_run_shell_command
from newcode.tools.display import display_non_streamed_result
from newcode.tools.file_modifications import register_delete_file, register_edit_file
from newcode.tools.file_operations import (
    register_grep,
    register_list_files,
    register_read_file,
)
from newcode.tools.skills_tools import (
    register_activate_skill,
    register_list_or_search_skills,
)
from newcode.tools.universal_constructor import register_universal_constructor

# Try to import CDP-based browser tools (requires websockets)
try:
    # Browser automation tools (CDP-based, replacing Playwright)
    from newcode.tools.browser.cdp_control import (
        register_close_browser as register_browser_close,
    )
    from newcode.tools.browser.cdp_control import (
        register_create_new_page as register_browser_new_page,
    )
    from newcode.tools.browser.cdp_control import (
        register_get_browser_status as register_browser_status,
    )
    from newcode.tools.browser.cdp_control import (
        register_initialize_browser as register_browser_initialize,
    )
    from newcode.tools.browser.cdp_control import (
        register_list_pages as register_browser_list_pages,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_browser_check,
        register_browser_uncheck,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_click_element as register_browser_click,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_double_click_element as register_browser_double_click,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_get_element_text as register_browser_get_text,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_get_element_value as register_browser_get_value,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_hover_element as register_browser_hover,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_select_option as register_browser_select_option,
    )
    from newcode.tools.browser.cdp_interactions import (
        register_set_element_text as register_browser_set_text,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_buttons as register_browser_find_buttons,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_by_label as register_browser_find_by_label,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_by_placeholder as register_browser_find_by_placeholder,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_by_role as register_browser_find_by_role,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_by_test_id as register_browser_find_by_test_id,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_by_text as register_browser_find_by_text,
    )
    from newcode.tools.browser.cdp_locators import (
        register_find_links as register_browser_find_links,
    )
    from newcode.tools.browser.cdp_locators import (
        register_run_xpath_query as register_browser_xpath_query,
    )
    from newcode.tools.browser.cdp_navigation import (
        register_browser_go_back,
        register_browser_go_forward,
    )
    from newcode.tools.browser.cdp_navigation import (
        register_get_page_info as register_browser_get_page_info,
    )
    from newcode.tools.browser.cdp_navigation import (
        register_navigate_to_url as register_browser_navigate,
    )
    from newcode.tools.browser.cdp_navigation import (
        register_reload_page as register_browser_reload,
    )
    from newcode.tools.browser.cdp_navigation import (
        register_wait_for_load_state as register_browser_wait_for_load,
    )
    from newcode.tools.browser.cdp_screenshot import (
        register_take_screenshot_and_analyze as register_browser_screenshot_analyze,
    )
    from newcode.tools.browser.cdp_scripts import (
        register_browser_clear_highlights,
        register_browser_highlight_element,
    )
    from newcode.tools.browser.cdp_scripts import (
        register_execute_javascript as register_browser_execute_js,
    )
    from newcode.tools.browser.cdp_scripts import (
        register_scroll_page as register_browser_scroll,
    )
    from newcode.tools.browser.cdp_scripts import (
        register_scroll_to_element as register_browser_scroll_to_element,
    )
    from newcode.tools.browser.cdp_scripts import (
        register_set_viewport_size as register_browser_set_viewport,
    )
    from newcode.tools.browser.cdp_scripts import (
        register_wait_for_element as register_browser_wait_for_element,
    )

    _CDP_AVAILABLE = True
except ImportError:
    # websockets not installed - CDP tools unavailable
    _CDP_AVAILABLE = False
    emit_warning(
        "CDP browser automation unavailable - 'websockets' package not installed. "
        "Install with: pip install websockets"
    )

    # Define stub functions that raise ImportError when called
    def _make_stub_function(name: str):
        def stub(*args, **kwargs):
            raise ImportError(
                "Browser automation requires 'websockets' package. "
                "Install with: pip install websockets"
            )

        stub.__name__ = name
        return stub

    # Browser Control stubs
    register_browser_initialize = _make_stub_function("register_browser_initialize")
    register_browser_close = _make_stub_function("register_browser_close")
    register_browser_status = _make_stub_function("register_browser_status")
    register_browser_new_page = _make_stub_function("register_browser_new_page")
    register_browser_list_pages = _make_stub_function("register_browser_list_pages")

    # Browser Navigation stubs
    register_browser_navigate = _make_stub_function("register_browser_navigate")
    register_browser_get_page_info = _make_stub_function(
        "register_browser_get_page_info"
    )
    register_browser_go_back = _make_stub_function("register_browser_go_back")
    register_browser_go_forward = _make_stub_function("register_browser_go_forward")
    register_browser_reload = _make_stub_function("register_browser_reload")
    register_browser_wait_for_load = _make_stub_function(
        "register_browser_wait_for_load"
    )

    # Browser Locators stubs
    register_browser_find_by_role = _make_stub_function("register_browser_find_by_role")
    register_browser_find_by_text = _make_stub_function("register_browser_find_by_text")
    register_browser_find_by_label = _make_stub_function(
        "register_browser_find_by_label"
    )
    register_browser_find_by_placeholder = _make_stub_function(
        "register_browser_find_by_placeholder"
    )
    register_browser_find_by_test_id = _make_stub_function(
        "register_browser_find_by_test_id"
    )
    register_browser_xpath_query = _make_stub_function("register_browser_xpath_query")
    register_browser_find_buttons = _make_stub_function("register_browser_find_buttons")
    register_browser_find_links = _make_stub_function("register_browser_find_links")

    # Browser Interactions stubs
    register_browser_click = _make_stub_function("register_browser_click")
    register_browser_double_click = _make_stub_function("register_browser_double_click")
    register_browser_hover = _make_stub_function("register_browser_hover")
    register_browser_set_text = _make_stub_function("register_browser_set_text")
    register_browser_get_text = _make_stub_function("register_browser_get_text")
    register_browser_get_value = _make_stub_function("register_browser_get_value")
    register_browser_select_option = _make_stub_function(
        "register_browser_select_option"
    )
    register_browser_check = _make_stub_function("register_browser_check")
    register_browser_uncheck = _make_stub_function("register_browser_uncheck")

    # Browser Scripts stubs
    register_browser_execute_js = _make_stub_function("register_browser_execute_js")
    register_browser_scroll = _make_stub_function("register_browser_scroll")
    register_browser_scroll_to_element = _make_stub_function(
        "register_browser_scroll_to_element"
    )
    register_browser_set_viewport = _make_stub_function("register_browser_set_viewport")
    register_browser_wait_for_element = _make_stub_function(
        "register_browser_wait_for_element"
    )
    register_browser_highlight_element = _make_stub_function(
        "register_browser_highlight_element"
    )
    register_browser_clear_highlights = _make_stub_function(
        "register_browser_clear_highlights"
    )

    # Browser Screenshot stubs
    register_browser_screenshot_analyze = _make_stub_function(
        "register_browser_screenshot_analyze"
    )


# Map of tool names to their individual registration functions
# These are the user-facing tool names that agents use
TOOL_REGISTRY = {
    # Agent Tools
    "list_agents": register_list_agents,
    "invoke_agent": register_invoke_agent,
    # File Operations
    "list_files": register_list_files,
    "read_file": register_read_file,
    "grep": register_grep,
    # File Modifications
    "edit_file": register_edit_file,
    "delete_file": register_delete_file,
    # Command Runner
    "agent_run_shell_command": register_agent_run_shell_command,
    # User Interaction
    "ask_user_question": register_ask_user_question,
    # Browser Control
    "browser_initialize": register_browser_initialize,
    "browser_close": register_browser_close,
    "browser_status": register_browser_status,
    "browser_new_page": register_browser_new_page,
    "browser_list_pages": register_browser_list_pages,
    # Browser Navigation
    "browser_navigate": register_browser_navigate,
    "browser_get_page_info": register_browser_get_page_info,
    "browser_go_back": register_browser_go_back,
    "browser_go_forward": register_browser_go_forward,
    "browser_reload": register_browser_reload,
    "browser_wait_for_load": register_browser_wait_for_load,
    # Browser Element Discovery
    "browser_find_by_role": register_browser_find_by_role,
    "browser_find_by_text": register_browser_find_by_text,
    "browser_find_by_label": register_browser_find_by_label,
    "browser_find_by_placeholder": register_browser_find_by_placeholder,
    "browser_find_by_test_id": register_browser_find_by_test_id,
    "browser_xpath_query": register_browser_xpath_query,
    "browser_find_buttons": register_browser_find_buttons,
    "browser_find_links": register_browser_find_links,
    # Browser Element Interactions
    "browser_click": register_browser_click,
    "browser_double_click": register_browser_double_click,
    "browser_hover": register_browser_hover,
    "browser_set_text": register_browser_set_text,
    "browser_get_text": register_browser_get_text,
    "browser_get_value": register_browser_get_value,
    "browser_select_option": register_browser_select_option,
    "browser_check": register_browser_check,
    "browser_uncheck": register_browser_uncheck,
    # Browser Scripts and Advanced Features
    "browser_execute_js": register_browser_execute_js,
    "browser_scroll": register_browser_scroll,
    "browser_scroll_to_element": register_browser_scroll_to_element,
    "browser_set_viewport": register_browser_set_viewport,
    "browser_wait_for_element": register_browser_wait_for_element,
    "browser_highlight_element": register_browser_highlight_element,
    "browser_clear_highlights": register_browser_clear_highlights,
    # Browser Screenshots
    "browser_screenshot_analyze": register_browser_screenshot_analyze,
    # Browser Workflows
    "browser_save_workflow": register_save_workflow,
    "browser_list_workflows": register_list_workflows,
    "browser_read_workflow": register_read_workflow,
    # Terminal Connection Tools
    "terminal_check_server": register_check_terminal_server,
    "terminal_open": register_open_terminal,
    "terminal_close": register_close_terminal,
    "start_api_server": register_start_api_server,
    # Terminal Command Execution Tools
    "terminal_run_command": register_run_terminal_command,
    "terminal_send_keys": register_send_terminal_keys,
    "terminal_wait_output": register_wait_terminal_output,
    # Terminal Screenshot Tools
    "terminal_screenshot_analyze": register_terminal_screenshot,
    "terminal_read_output": register_terminal_read_output,
    "terminal_compare_mockup": register_terminal_compare_mockup,
    "load_image_for_analysis": register_load_image,
    # Skills Tools
    "activate_skill": register_activate_skill,
    "list_or_search_skills": register_list_or_search_skills,
    # Universal Constructor
    "universal_constructor": register_universal_constructor,
}


def _load_plugin_tools() -> None:
    """Load tools registered by plugins via the register_tools callback.

    This merges plugin-provided tools into the TOOL_REGISTRY.
    Called lazily when tools are first accessed.
    """
    try:
        results = on_register_tools()
        for result in results:
            if result is None:
                continue
            # Each result should be a list of tool definitions
            tools_list = result if isinstance(result, list) else [result]
            for tool_def in tools_list:
                if (
                    isinstance(tool_def, dict)
                    and "name" in tool_def
                    and "register_func" in tool_def
                ):
                    tool_name = tool_def["name"]
                    register_func = tool_def["register_func"]
                    if callable(register_func):
                        TOOL_REGISTRY[tool_name] = register_func
    except Exception:
        # Don't let plugin failures break core functionality
        pass


def register_tools_for_agent(
    agent, tool_names: list[str], model_name: str | None = None
):
    """Register specific tools for an agent based on tool names.

    Args:
        agent: The agent to register tools to.
        tool_names: List of tool names to register. UC tools are prefixed with "uc:".
        model_name: Optional model name for conditional tool filtering.
    """
    from newcode.config import get_universal_constructor_enabled

    _load_plugin_tools()

    for tool_name in tool_names:
        # Handle UC tools (prefixed with "uc:")
        if tool_name.startswith("uc:"):
            # Skip UC tools if UC is disabled
            if not get_universal_constructor_enabled():
                continue
            uc_tool_name = tool_name[3:]  # Remove "uc:" prefix
            _register_uc_tool_wrapper(agent, uc_tool_name)
            continue

        if tool_name not in TOOL_REGISTRY:
            # Skip unknown tools with a warning instead of failing
            emit_warning(f"Warning: Unknown tool '{tool_name}' requested, skipping...")
            continue

        # Check if Universal Constructor is disabled
        if (
            tool_name == "universal_constructor"
            and not get_universal_constructor_enabled()
        ):
            continue  # Skip UC if disabled in config

        # Register the individual tool
        register_func = TOOL_REGISTRY[tool_name]
        register_func(agent)


def _register_uc_tool_wrapper(agent, uc_tool_name: str):
    """Register a wrapper for a UC tool that calls it via the UC registry.

    This creates a dynamic tool that wraps the UC tool, preserving its
    parameter signature so pydantic-ai can generate proper JSON schema.

    Args:
        agent: The agent to register the tool wrapper to.
        uc_tool_name: The full name of the UC tool (e.g., "api.weather").
    """
    import inspect
    from typing import Any

    from pydantic_ai import RunContext

    # Get tool info and function from registry
    try:
        from newcode.plugins.universal_constructor.registry import get_registry

        registry = get_registry()
        tool_info = registry.get_tool(uc_tool_name)
        if not tool_info:
            emit_warning(f"Warning: UC tool '{uc_tool_name}' not found, skipping...")
            return

        func = registry.get_tool_function(uc_tool_name)
        if not func:
            emit_warning(
                f"Warning: UC tool '{uc_tool_name}' function not found, skipping..."
            )
            return

        description = tool_info.meta.description
        docstring = tool_info.docstring or description
    except Exception as e:
        emit_warning(f"Warning: Failed to get UC tool '{uc_tool_name}' info: {e}")
        return

    # Get the original function's signature
    try:
        sig = inspect.signature(func)
        # Get annotations from the original function
        annotations = getattr(func, "__annotations__", {}).copy()
    except (ValueError, TypeError):
        sig = None
        annotations = {}

    # Create wrapper that preserves the signature
    def make_uc_wrapper(
        tool_name: str, original_func, original_sig, original_annotations
    ):
        # Build the wrapper function
        async def uc_tool_wrapper(context: RunContext, **kwargs: Any) -> Any:
            """Dynamically generated wrapper for a UC tool."""
            try:
                result = original_func(**kwargs)
                # Await async tool implementations
                if inspect.isawaitable(result):
                    result = await result
                return result
            except Exception as e:
                return {"error": f"UC tool '{tool_name}' failed: {e}"}

        # Copy signature info from original function
        uc_tool_wrapper.__name__ = tool_name.replace(".", "_")
        uc_tool_wrapper.__doc__ = (
            f"{docstring}\n\nThis is a Universal Constructor tool."
        )

        # Preserve annotations for pydantic-ai schema generation
        if original_annotations:
            # Add 'context' param and copy original params (excluding 'return')
            new_annotations = {"context": RunContext}
            for param_name, param_type in original_annotations.items():
                if param_name != "return":
                    new_annotations[param_name] = param_type
            if "return" in original_annotations:
                new_annotations["return"] = original_annotations["return"]
            else:
                new_annotations["return"] = Any
            uc_tool_wrapper.__annotations__ = new_annotations

        # Try to set __signature__ for better introspection
        if original_sig:
            try:
                # Build new parameters list: context first, then original params
                new_params = [
                    inspect.Parameter(
                        "context",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=RunContext,
                    )
                ]
                for param in original_sig.parameters.values():
                    new_params.append(param)

                # Create new signature with return annotation
                return_annotation = original_annotations.get("return", Any)
                new_sig = original_sig.replace(
                    parameters=new_params, return_annotation=return_annotation
                )
                uc_tool_wrapper.__signature__ = new_sig
            except (ValueError, TypeError):
                pass  # Signature manipulation failed, continue without it

        return uc_tool_wrapper

    wrapper = make_uc_wrapper(uc_tool_name, func, sig, annotations)

    # Register the wrapper as a tool
    try:
        agent.tool(wrapper)
    except Exception as e:
        emit_warning(f"Warning: Failed to register UC tool '{uc_tool_name}': {e}")


def register_all_tools(agent, model_name: str | None = None):
    """Register all available tools to the provided agent.

    Args:
        agent: The agent to register tools to.
        model_name: Optional model name for conditional tool filtering.
    """
    all_tools = list(TOOL_REGISTRY.keys())
    register_tools_for_agent(agent, all_tools, model_name=model_name)


def get_available_tool_names() -> list[str]:
    """Get list of all available tool names.

    Returns:
        List of all tool names that can be registered.
    """
    _load_plugin_tools()
    return list(TOOL_REGISTRY.keys())
