tools_content = """
Here is the complete set of available tools:

# **File Operations**
- **`list_files(directory, recursive)`** - Browse directories showing files, directories, sizes, and depth
- **`read_file(file_path)`** - Read any file content (with line count info)
- **`edit_file(path, diff)`** - Edit files with support for:
  - Creating new files
  - Overwriting entire files
  - Making targeted replacements (preferred method)
  - Deleting specific snippets
- **`delete_file(file_path)`** - Remove files when needed (use with caution)

# **Search & Analysis**
- **`grep(search_string, directory)`** - Search for text across files recursively using ripgrep (rg) for high-performance searching (up to 200 matches). Searches across all text file types, not just Python files. Supports ripgrep flags in the search string.

# **System Operations**
- **`agent_run_shell_command(command, cwd, timeout)`** - Execute shell commands with full output capture (stdout, stderr, exit codes)

# **Network Operations**
- **`grab_json_from_url(url)`** - Fetch JSON data from URLs (when network allows)

# **Agent Communication**
- **`agent_share_your_reasoning(reasoning, next_steps)`** - Share the reasoning process and planned next steps (transparency)
- **`final_result(output_message, awaiting_user_input)`** - Deliver final responses

# **Tool Usage Philosophy**

These principles are followed:
- **DRY** - Don't Repeat Yourself
- **YAGNI** - You Ain't Gonna Need It
- **SOLID** - Single responsibility, Open/closed, etc.
- **Files under 600 lines** - Keep things manageable

# **Pro Tips**

- For `edit_file`, **targeted replacements** are preferred over full file overwrites (more efficient)
- `agent_share_your_reasoning` is used before major operations to explain the thinking
- When running tests, `--silent` flags for JS/TS are used to avoid spam
- Explore with `list_files` before modifying anything

# **Capabilities**

With these tools, the agent can:
- Write, modify, and organize code
- Analyze codebases and find patterns
- Run tests and debug issues
- Generate documentation and reports
- Automate development workflows
- Refactor code following best practices
"""
