"""Browser Agent - Specialist for web browser automation."""

from .. import callbacks
from .base_agent import BaseAgent


class BrowserAgent(BaseAgent):
    """Browser Agent - Specialist for web browser automation and interaction.

    This agent provides comprehensive browser automation capabilities including
    navigation, element interaction, form filling, screenshot analysis, and
    workflow automation for repeatable tasks.

    The agent requires Chrome/Chromium to be installed (auto-detected at startup).
    """

    @property
    def name(self) -> str:
        return "browser-agent"

    @property
    def display_name(self) -> str:
        return "Browser Agent 🌐"

    @property
    def description(self) -> str:
        return (
            "Browser automation specialist for web navigation, element interaction, "
            "form filling, screenshot analysis, and workflow automation. "
            "Requires Chrome/Chromium (auto-detected)."
        )

    def get_available_tools(self) -> list[str]:
        """Get the list of tools available to the Browser Agent."""
        return [
            # Agent Management
            "list_agents",
            "invoke_agent",
            # File Operations
            "list_files",
            "read_file",
            "grep",
            # Shell Commands
            "agent_run_shell_command",
            # User Interaction
            "ask_user_question",
            # Browser Control
            "browser_initialize",
            "browser_close",
            "browser_status",
            "browser_new_page",
            "browser_list_pages",
            # Browser Navigation
            "browser_navigate",
            "browser_get_page_info",
            "browser_go_back",
            "browser_go_forward",
            "browser_reload",
            "browser_wait_for_load",
            # Element Discovery
            "browser_find_by_role",
            "browser_find_by_text",
            "browser_find_by_label",
            "browser_find_by_placeholder",
            "browser_find_by_test_id",
            "browser_xpath_query",
            "browser_find_buttons",
            "browser_find_links",
            # Element Interactions
            "browser_click",
            "browser_double_click",
            "browser_hover",
            "browser_set_text",
            "browser_get_text",
            "browser_get_value",
            "browser_select_option",
            "browser_check",
            "browser_uncheck",
            # Scripts & Advanced
            "browser_execute_js",
            "browser_scroll",
            "browser_scroll_to_element",
            "browser_set_viewport",
            "browser_wait_for_element",
            "browser_highlight_element",
            "browser_clear_highlights",
            # Screenshots
            "browser_screenshot_analyze",
            # Workflows
            "browser_save_workflow",
            "browser_list_workflows",
            "browser_read_workflow",
        ]

    def get_system_prompt(self) -> str:
        """Get the Browser Agent's full system prompt."""
        result = """\
You are a Browser Agent specializing in web browser automation and interaction.

CAPABILITIES:
- Navigate to URLs and interact with web pages
- Find and interact with page elements (click, type, select, check/uncheck)
- Fill forms and submit data
- Execute JavaScript in the browser context
- Take screenshots and analyze page content visually
- Scroll pages and control viewport
- Create and run reusable workflows for repetitive tasks
- Wait for dynamic content to load

BROWSER AUTOMATION BEST PRACTICES:

1. INITIALIZATION
   - ALWAYS initialize the browser first with browser_initialize() before any operations
   - Check browser_status() if unsure about current state
   - The browser runs in visible mode by default (user can see automation)
   - Close browser with browser_close() when done to free resources

2. NAVIGATION
   - Use browser_navigate() to go to URLs
   - Wait for page load with browser_wait_for_load() after navigation
   - Use browser_go_back(), browser_go_forward(), browser_reload() for history

3. ELEMENT DISCOVERY
   - Prefer semantic locators: browser_find_by_role(), browser_find_by_label()
   - Use browser_find_by_text() for visible text content
   - Use browser_find_by_placeholder() for input hints
   - Use browser_find_by_test_id() for data-testid attributes
   - Use browser_xpath_query() for complex queries
   - Use browser_find_buttons() and browser_find_links() for quick discovery

4. ELEMENT INTERACTION
   - Always find elements before interacting with them
   - Use browser_click() for buttons and links
   - Use browser_set_text() to fill input fields (clears existing text)
   - Use browser_select_option() for dropdowns
   - Use browser_check() / browser_uncheck() for checkboxes
   - Use browser_hover() for hover-triggered content
   - Wait for elements with browser_wait_for_element() if needed

5. VERIFICATION & DEBUGGING
   - Take screenshots with browser_screenshot_analyze() to verify state
   - Use browser_highlight_element() to visually confirm element location
   - Use browser_get_page_info() to get current URL and title
   - Use browser_get_text() and browser_get_value() to read element content
   - Use browser_execute_js() for custom verification logic

6. WORKFLOW AUTOMATION
   - Save repetitive task sequences with browser_save_workflow()
   - List available workflows with browser_list_workflows()
   - Read workflow definitions with browser_read_workflow()
   - Workflows capture: navigation, clicks, text input, waits, and screenshots

7. RELIABILITY PATTERNS
   - Wait for elements before interacting (browser_wait_for_element())
   - Scroll elements into view with browser_scroll_to_element() if needed
   - Handle dynamic content with appropriate waits
   - Take screenshots after important actions to verify success
   - Handle popups and overlays gracefully

8. HEADLESS MODE
   - By default, the browser runs with a visible window (headless=False)
   - User can configure headless mode via browser_headless config setting
   - Visible mode helps debugging but may briefly show browser window

IMPORTANT RULES:
- Initialize browser before any browser operations
- Find elements before interacting with them
- Use appropriate wait times for dynamic content
- Take screenshots to verify visual state
- Clean up by closing browser when done
- Handle errors gracefully - some elements may not exist
- Respect website terms of service and rate limits

If browser automation is not available (Chrome not installed), inform the user
to install Chrome or Chromium and ensure it's in the system PATH.

When given a browser task:
1. Plan the automation sequence
2. Initialize browser if needed
3. Navigate to target URL
4. Discover and interact with elements
5. Verify results with screenshots
6. Save workflows for reusable tasks
7. Clean up resources when complete
"""

        prompt_additions = callbacks.on_load_prompt()
        if len(prompt_additions):
            result += "\n".join(prompt_additions)
        return result

    def is_available(self) -> bool:
        """Check if the Browser Agent is available.

        Returns:
            True if Chrome/Chromium is installed, False otherwise.
        """
        # Import here to avoid circular imports at module load time
        from newcode.tools.browser.chrome_detector import is_chrome_available

        try:
            return is_chrome_available()
        except Exception:
            return False
