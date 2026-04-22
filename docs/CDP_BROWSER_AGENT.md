# CDP Browser Agent Implementation

A complete Chrome DevTools Protocol (CDP) based browser automation system for the newcode agent platform. This implementation provides direct WebSocket communication with Chrome, eliminating the Playwright abstraction layer while maintaining full browser automation capabilities.

## Table of Contents

1. [What is CDP Browser Agent?](#what-is-cdp-browser-agent)
2. [Architecture Overview](#architecture-overview)
3. [File Structure](#file-structure)
4. [Configuration](#configuration)
5. [Chrome Detection Priority](#chrome-detection-priority)
6. [How It Works](#how-it-works)
7. [Usage Examples](#usage-examples)
8. [Comparison: CDP vs Playwright](#comparison-cdp-vs-playwright)
9. [Migration Notes](#migration-notes)
10. [Requirements](#requirements)

---

## What is CDP Browser Agent?

The **CDP Browser Agent** is a browser automation system that directly uses the Chrome DevTools Protocol (CDP) via WebSocket connections. Unlike the previous Playwright-based implementation, this approach communicates directly with Chrome's debugging interface, providing:

- **Direct Protocol Access**: No abstraction layer between the agent and Chrome
- **Full CDP Feature Set**: Access to all Chrome DevTools capabilities
- **WebSocket Communication**: JSON-RPC 2.0 over WebSocket for real-time control
- **Similar to chrome-devtools-rust**: Inspired by Rust CDP implementations but written in Python
- **Process Control**: Direct Chrome process lifecycle management

### Key Features

- **39 Browser Automation Tools**: Complete set of browser control, navigation, element discovery, interaction, and scripting tools
- **Per-Session Isolation**: Each session gets its own Chrome instance for clean state management
- **Auto-Detection**: Automatically finds and uses system Chrome, or falls back to Playwright's bundled Chromium
- **Headless/Visible Mode**: Configurable headless operation via `/set browser_headless`

---

## Architecture Overview

The CDP browser agent is organized into four main layers:

```
┌─────────────────────────────────────────────────────────┐
│                    Tool Layer                           │
│  (39 browser tools: click, navigate, screenshot, etc.)  │
├─────────────────────────────────────────────────────────┤
│                  CDP Domains Layer                      │
│  (PageDomain, DOMDomain, RuntimeDomain, etc.)          │
├─────────────────────────────────────────────────────────┤
│                  CDP Manager Layer                      │
│  (Chrome process management, port allocation)            │
├─────────────────────────────────────────────────────────┤
│                  CDP Client Layer                       │
│  (WebSocket connection, JSON-RPC 2.0 protocol)         │
└─────────────────────────────────────────────────────────┘
```

### 1. CDPClient (WebSocket Client)

**File**: `cdp_client.py`

The foundational WebSocket client that handles CDP communication:

- **WebSocket Connection**: Connects to `ws://localhost:9222/devtools/browser`
- **JSON-RPC 2.0**: Formats and sends CDP commands with incremental IDs
- **Event Handling**: Subscribes to CDP events (e.g., `Page.loadEventFired`)
- **Auto-Reconnection**: Handles connection failures and retries
- **Context Manager**: `async with` support for clean resource management

**Key Methods**:
```python
await client.connect(host, port)           # Connect to Chrome
await client.disconnect()                  # Close connection
response = await client.send_command(method, params)  # Send CDP command
client.on_event(event_name, callback)      # Subscribe to events
```

### 2. CDPManager (Process Management)

**File**: `cdp_manager.py`

Manages Chrome process lifecycle and session state:

- **Chrome Launch**: Starts Chrome with `--remote-debugging-port=PORT`
- **Port Detection**: Auto-detects available ports (starts at 9222)
- **Session Tracking**: Per-session browser instances
- **Cleanup**: Automatic cleanup via `atexit` handlers
- **Connection Management**: Maintains CDPClient instances per session

**Key Functions**:
```python
manager = get_cdp_manager(session_id)      # Get or create manager
await manager.launch(headless=True)        # Launch Chrome
await manager.close()                       # Shutdown Chrome
client = manager.get_client()               # Get CDPClient for commands
```

### 3. CDP Domains (Protocol Wrappers)

**File**: `cdp_domains.py`

Pythonic wrappers for CDP protocol domains:

| Domain | Purpose | Key Methods |
|--------|---------|-------------|
| `PageDomain` | Page navigation and control | `navigate()`, `reload()`, `goBack()`, `goForward()`, `captureScreenshot()` |
| `DOMDomain` | DOM inspection and querying | `querySelector()`, `getDocument()`, `describeNode()`, `requestNode()` |
| `RuntimeDomain` | JavaScript execution | `evaluate()` - Execute JS code |
| `InputDomain` | User input simulation | `dispatchMouseEvent()`, `dispatchKeyEvent()` |
| `TargetDomain` | Page/target management | `createTarget()`, `getTargets()`, `closeTarget()` |

Each domain takes a `CDPClient` instance and provides high-level Python methods that map to CDP protocol commands.

**Example**:
```python
page = PageDomain(client)
await page.navigate("https://example.com")
await page.reload()

runtime = RuntimeDomain(client)
result = await runtime.evaluate("document.title")
```

### 4. Tool Layer (Browser Tools)

The 39 browser automation tools are organized into categories:

- **cdp_control.py**: Initialize, close, status, page management (5 tools)
- **cdp_navigation.py**: Navigate, back, forward, reload, wait (6 tools)
- **cdp_locators.py**: Element discovery by role, text, label, etc. (8 tools)
- **cdp_interactions.py**: Click, type, select, hover (9 tools)
- **cdp_scripts.py**: JavaScript execution, scrolling, highlighting (8 tools)
- **cdp_screenshot.py**: Screenshot capture with analysis (1 tool)
- **cdp_workflows.py**: Workflow recording and replay (3 tools)

---

## File Structure

### New CDP Implementation Files

All files are located in `newcode/tools/browser/`:

| File | Purpose | Lines |
|------|---------|-------|
| `cdp_client.py` | WebSocket CDP client with JSON-RPC 2.0 | ~500 |
| `cdp_manager.py` | Chrome process lifecycle management | ~550 |
| `cdp_domains.py` | CDP domain wrappers (Page, DOM, Runtime, Input, Target) | ~950 |
| `cdp_control.py` | Browser control tools (init, close, status, pages) | ~320 |
| `cdp_navigation.py` | Navigation tools (navigate, back, forward, reload) | ~280 |
| `cdp_locators.py` | Element discovery tools (find by role, text, xpath) | ~680 |
| `cdp_interactions.py` | Element interaction tools (click, type, select) | ~620 |
| `cdp_screenshot.py` | Screenshot capture with AI analysis | ~250 |
| `cdp_scripts.py` | JavaScript execution and advanced features | ~460 |

### Supporting Files

| File | Purpose |
|------|---------|
| `chrome_detector.py` | Chrome/Chromium detection (system & Playwright) |
| `browser_workflows.py` | Workflow management (markdown-based) |
| `chromium_terminal_manager.py` | Terminal automation (still used) |

### Retired Playwright Files

Moved to `newcode/agents/_retired/tools/browser/`:

- `browser_manager.py` - Playwright browser session management
- `browser_control.py` - Playwright control tools
- `browser_navigation.py` - Playwright navigation
- `browser_locators.py` - Playwright element locators
- `browser_interactions.py` - Playwright interactions
- `browser_screenshot.py` - Playwright screenshots
- `browser_scripts.py` - Playwright script execution

---

## Configuration

Browser configuration is managed via the `/set` command or configuration file:

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `browser_headless` | bool | `false` | Run Chrome without visible window |
| `browser_chrome_path` | str | `null` | Custom Chrome/Chromium executable path |
| `browser_agent_enabled` | bool | auto | Auto-detected at startup based on Chrome availability |

### Setting Configuration

```bash
# Enable headless mode (no visible browser window)
/set browser_headless true

# Set custom Chrome path
/set browser_chrome_path /usr/bin/google-chrome

# Disable headless mode (show browser window)
/set browser_headless false
```

### Viewing Configuration

```bash
/config browser_headless
/config browser_chrome_path
/config browser_agent_enabled
```

---

## Chrome Detection Priority

Chrome detection follows this priority order at startup:

1. **Custom Chrome Path** (`browser_chrome_path` config)
   - If set, uses this path exclusively
   - Useful for custom Chrome installations or specific versions

2. **System Chrome/Chromium** (OS-specific detection)
   - **macOS**: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
   - **Linux**: `google-chrome`, `chromium`, `chromium-browser` (searches PATH)
   - **Windows**: Registry lookup for Chrome installations

3. **Playwright Bundled Chromium** (fallback)
   - Uses Playwright's bundled browser if available
   - Ensures browser automation works even without system Chrome

### Startup Messages

**Chrome Available**:
```
✓ Chrome detected (System): /Applications/Google Chrome.app/Contents/MacOS/Google Chrome (v147.0.7727.102)
  Browser headless mode: disabled (visible window)
```

**Chrome Not Available**:
```
⚠️  Chrome/Chromium not found. Browser automation tools are disabled.
   Install Chrome/Chromium or run 'playwright install chromium' to enable browser-agent.
```

---

## How It Works

### 1. Chrome Launch

When `initialize_browser()` is called:

```python
# Chrome is launched with remote debugging enabled
chrome_args = [
    "--remote-debugging-port=9222",  # Enable CDP
    "--headless=new",                 # Headless mode (if enabled)
    "--no-first-run",                 # Skip first run UI
    "--no-default-browser-check",     # Skip default browser prompt
    "--disable-default-apps",          # Disable default apps
]
```

### 2. WebSocket Connection

The CDPClient connects to Chrome's debugging endpoint:

```python
ws_uri = "ws://localhost:9222/devtools/browser"
# JSON-RPC 2.0 protocol over WebSocket
```

### 3. CDP Command Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Your Code  │────▶│  CDPClient   │────▶│   Chrome    │
│             │◀────│  (WebSocket)│◀────│  (CDP Port) │
└─────────────┘     └─────────────┘     └─────────────┘
      │                                           │
      │                                           │
      ▼                                           ▼
await page.navigate(                        Receives:
  "https://example.com")                    {"method": "Page.navigate",
                                               "params": {"url": "..."}}
                                              
      │                                           │
      │◀──────────────────────────────────────────┘
      │
      ▼
Receives response:
{"id": 1, "result": {"frameId": "...", "loaderId": "..."}}
```

### 4. Event Handling

CDP events are handled via callbacks:

```python
# Subscribe to page load events
client.on_event("Page.loadEventFired", lambda event: print("Page loaded!"))

# Enable the domain first
await client.send_command("Page.enable")
```

### 5. Protocol Examples

**Navigate to URL**:
```json
{
  "method": "Page.navigate",
  "params": {"url": "https://example.com"},
  "id": 1
}
```

**Evaluate JavaScript**:
```json
{
  "method": "Runtime.evaluate",
  "params": {"expression": "document.title"},
  "id": 2
}
```

**Dispatch Mouse Event**:
```json
{
  "method": "Input.dispatchMouseEvent",
  "params": {
    "type": "mousePressed",
    "x": 100,
    "y": 200,
    "button": "left",
    "clickCount": 1
  },
  "id": 3
}
```

---

## Usage Examples

### Basic Navigation

```python
from newcode.tools.browser import get_cdp_manager
from newcode.tools.browser.cdp_domains import PageDomain

async def navigate_example():
    # Get CDP manager for this session
    manager = get_cdp_manager("my-session")
    
    # Launch Chrome
    await manager.launch(headless=False)
    
    # Get page domain
    page = PageDomain(manager.get_client())
    
    # Navigate to URL
    await page.navigate("https://example.com")
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Get page info
    info = await page.get_page_info()
    print(f"Title: {info['title']}")
    print(f"URL: {info['url']}")
    
    # Cleanup
    await manager.close()
```

### Element Interaction

```python
from newcode.tools.browser.cdp_domains import DOMDomain, InputDomain

async def click_example(client):
    dom = DOMDomain(client)
    input_domain = InputDomain(client)
    
    # Query element
    node_id = await dom.query_selector("button.submit")
    
    # Get element position
    node_info = await dom.get_node_info(node_id)
    box = node_info["bounding_box"]
    
    # Click at center of element
    await input_domain.dispatch_mouse_event(
        "mousePressed",
        box["center_x"],
        box["center_y"]
    )
    await input_domain.dispatch_mouse_event(
        "mouseReleased",
        box["center_x"],
        box["center_y"]
    )
```

### JavaScript Execution

```python
from newcode.tools.browser.cdp_domains import RuntimeDomain

async def js_example(client):
    runtime = RuntimeDomain(client)
    
    # Execute JavaScript
    result = await runtime.evaluate("document.title")
    print(f"Page title: {result}")
    
    # Execute with return value
    result = await runtime.evaluate("document.querySelectorAll('a').length")
    print(f"Number of links: {result}")
    
    # Execute complex script
    script = """
    (function() {
        const data = {
            url: window.location.href,
            title: document.title,
            links: Array.from(document.querySelectorAll('a')).map(a => a.href)
        };
        return data;
    })()
    """
    result = await runtime.evaluate(script)
    print(result)
```

### Screenshot Capture

```python
from newcode.tools.browser.cdp_domains import PageDomain

async def screenshot_example(client):
    page = PageDomain(client)
    
    # Capture screenshot
    screenshot_data = await page.capture_screenshot(
        format="png",
        full_page=True
    )
    
    # Save to file
    with open("screenshot.png", "wb") as f:
        f.write(screenshot_data)
```

### Using Browser Tools (Agent Integration)

```python
# Agents use the browser tools directly
# Example: browser_click tool

from newcode.tools.browser.cdp_interactions import click_element

async def agent_click_example():
    result = await click_element(
        session_id="my-session",
        element_id="button-123",
        click_type="single"
    )
    print(result)
```

---

## Comparison: CDP vs Playwright

| Aspect | CDP (Direct) | Playwright (Abstraction) |
|--------|--------------|--------------------------|
| **Protocol Access** | Direct WebSocket to Chrome | Uses CDP internally, adds abstraction layer |
| **Control Level** | Full control over all CDP features | Limited to Playwright's API surface |
| **Performance** | Minimal overhead, direct communication | Additional layer, slightly more overhead |
| **Dependencies** | Only `websockets` package | Full Playwright library + browsers |
| **Bundle Size** | Smaller (just websockets) | Larger (includes browser binaries) |
| **API Stability** | Chrome's protocol changes | Playwright maintains stable API |
| **Flexibility** | Access to all CDP domains | Limited to Playwright's implemented features |
| **Learning Curve** | Requires CDP knowledge | Higher-level, easier to use |
| **Maintenance** | We maintain the CDP wrappers | Microsoft maintains Playwright |

### When to Use CDP

- Need direct access to Chrome DevTools features
- Want to minimize dependencies
- Building custom browser automation
- Need fine-grained control over browser behavior

### When Playwright Might Be Better

- Want a stable, maintained API
- Don't want to deal with protocol changes
- Need cross-browser support (Firefox, WebKit)
- Prefer higher-level abstractions

---

## Migration Notes

### What Changed

1. **Implementation Layer**: Playwright → Direct CDP
2. **Communication**: Playwright API → WebSocket JSON-RPC 2.0
3. **Process Management**: Playwright-managed → Our CDPManager
4. **File Organization**: Playwright files moved to `_retired/`

### What Stayed the Same

1. **Tool API**: Same 39 tool names and signatures
2. **Agent Integration**: Agents use tools the same way
3. **Configuration**: Same `/set browser_*` commands
4. **Chrome Detection**: Still auto-detects system Chrome
5. **Session Management**: Still per-session browser instances

### Backward Compatibility

The migration maintains full backward compatibility:

- Existing agent code using browser tools continues to work
- Same tool names: `browser_click`, `browser_navigate`, etc.
- Same configuration keys: `browser_headless`, `browser_chrome_path`
- Same agent: `browser-agent` with same capabilities

### Migration Path for Playwright Code

If you have custom code using Playwright:

```python
# Old (Playwright)
from newcode.tools.browser.browser_manager import get_session_browser_manager

manager = get_session_browser_manager(session_id)
browser = await manager.get_browser()
page = await browser.new_page()
await page.goto("https://example.com")

# New (CDP)
from newcode.tools.browser import get_cdp_manager
from newcode.tools.browser.cdp_domains import PageDomain

manager = get_cdp_manager(session_id)
await manager.launch()
page = PageDomain(manager.get_client())
await page.navigate("https://example.com")
```

---

## Requirements

### Python Dependencies

```toml
# In pyproject.toml
dependencies = [
    "websockets>=14.0",  # WebSocket client for CDP
    # ... other dependencies
]
```

### Chrome/Chromium

One of the following must be available:

1. **Google Chrome** (recommended)
   - macOS: Install from [google.com/chrome](https://google.com/chrome)
   - Linux: `sudo apt install google-chrome-stable`
   - Windows: Download from Google

2. **Chromium**
   - macOS: `brew install chromium`
   - Linux: `sudo apt install chromium-browser`

3. **Playwright Bundled Chromium** (fallback)
   - Install with: `playwright install chromium`

### Startup Detection

On application startup, the system:

1. Detects Chrome using the [Chrome Detection Priority](#chrome-detection-priority)
2. Sets `browser_agent_enabled` config based on availability
3. Shows status message (✓ available or ⚠️ not found)
4. Browser-agent is hidden from `list_agents` if Chrome is not available

---

## Troubleshooting

### Chrome Not Found

**Symptom**: "⚠️ Chrome/Chromium not found" at startup

**Solutions**:
1. Install Chrome from [google.com/chrome](https://google.com/chrome)
2. Or run: `playwright install chromium`
3. Or set custom path: `/set browser_chrome_path /path/to/chrome`

### WebSocket Connection Failed

**Symptom**: CDP connection errors

**Solutions**:
1. Check if Chrome started successfully
2. Verify port 9222 is available (will auto-increment if taken)
3. Check Chrome logs for startup errors

### Headless Mode Issues

**Symptom**: Browser not visible when expected (or vice versa)

**Solutions**:
- Check `/set browser_headless` value
- `true` = no visible window (headless)
- `false` = visible window (default)

---

## Additional Resources

- [Chrome DevTools Protocol Viewer](https://chromedevtools.github.io/devtools-protocol/)
- [CDP Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/)
- [chrome-devtools-rust](https://github.com/angelo-loria/chrome-devtools-rust) - Rust CDP implementation (inspiration)

---

## Summary

The CDP Browser Agent provides a modern, lightweight browser automation system for the newcode platform:

- **Direct CDP Access**: WebSocket communication with Chrome
- **39 Browser Tools**: Complete automation capabilities
- **Zero Playwright Dependency**: Uses only `websockets` package
- **Auto-Detection**: Finds system Chrome or uses Playwright fallback
- **Per-Session Isolation**: Clean state management
- **Full Backward Compatibility**: Same APIs as before

The implementation follows the philosophy of direct protocol access while maintaining ease of use through high-level Pythonic wrappers.
