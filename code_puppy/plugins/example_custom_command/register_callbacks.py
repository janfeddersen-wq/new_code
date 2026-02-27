from code_puppy.callbacks import register_callback
from code_puppy.messaging import emit_info


def _custom_help():
    return [
        ("hello", "Send a greeting message (no model)"),
        ("echo", "Echo back your text (display only)"),
    ]


def _handle_custom_command(command: str, name: str):
    """Handle a demo custom command.

    Policy: custom commands must NOT invoke the model. They should emit
    messages or return True to indicate handling. Returning a string is
    treated as a display-only message by the command handler.

    Supports:
    - /hello        -> emits a greeting and returns True
    - /echo <text>  -> emits the text (display-only)
    """
    if not name:
        return None

    if name == "hello":
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            text = parts[1]
            emit_info(f"Sending prompt: {text}")
            return text
        emit_info("Sending prompt: Tell me something interesting")
        return "Tell me something interesting"

    if name == "echo":
        rest = command.split(maxsplit=1)
        if len(rest) == 2:
            text = rest[1]
            emit_info(f"example plugin echo -> {text}")
            return text
        emit_info("example plugin echo (empty)")
        return ""

    return None


register_callback("custom_command_help", _custom_help)
register_callback("custom_command", _handle_custom_command)
